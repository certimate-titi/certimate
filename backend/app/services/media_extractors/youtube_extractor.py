"""YouTube extractor — yt-dlp subtitles with Whisper API fallback."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)


class YouTubeExtractor:
    """Extract transcript from YouTube videos.

    Strategy:
    1. yt-dlp: try to download existing subtitles (auto or manual)
    2. Whisper fallback: download audio → transcribe via OpenAI Whisper API
    """

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        """file_path here is actually the YouTube URL."""
        youtube_url = file_path

        # Step 1: Try yt-dlp subtitles
        transcript = self._get_subtitles(youtube_url)
        video_title = self._get_video_title(youtube_url) or resource_name or youtube_url

        if transcript:
            logger.info("YouTube subtitles extracted via yt-dlp (%d chars)", len(transcript))
            return ExtractionResult(
                title=video_title,
                content_type="transcript",
                raw_text=transcript,
                metadata=f"source:youtube_subtitle,url:{youtube_url}",
            )

        # Step 2: Whisper fallback — download audio and transcribe
        logger.info("No subtitles found, falling back to Whisper API")
        transcript = self._whisper_fallback(youtube_url)

        return ExtractionResult(
            title=video_title,
            content_type="transcript",
            raw_text=transcript,
            metadata=f"source:youtube_whisper,url:{youtube_url}",
        )

    @staticmethod
    def _get_video_title(youtube_url: str) -> str | None:
        """Get video title using yt-dlp."""
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return info.get("title", "")
        except Exception as e:
            logger.warning("Failed to get YouTube title: %s", e)
            return None

    @staticmethod
    def _get_subtitles(youtube_url: str) -> str | None:
        """Try to download subtitles using yt-dlp."""
        try:
            import yt_dlp

            tmp_dir = tempfile.mkdtemp(prefix="yt_subs_")
            output_template = os.path.join(tmp_dir, "%(id)s")

            ydl_opts = {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["zh-TW", "zh-Hant", "zh", "zh-Hans", "en"],
                "subtitlesformat": "vtt",
                "skip_download": True,
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])

            # Find downloaded subtitle file
            sub_files = list(Path(tmp_dir).glob("*.vtt"))
            if not sub_files:
                sub_files = list(Path(tmp_dir).glob("*.srt"))

            if not sub_files:
                return None

            # Parse the best subtitle file (prefer zh-TW)
            best_file = sub_files[0]
            for f in sub_files:
                if "zh-TW" in f.name or "zh-Hant" in f.name:
                    best_file = f
                    break

            raw_sub = best_file.read_text(encoding="utf-8", errors="ignore")
            return _parse_vtt(raw_sub)

        except ImportError:
            logger.warning("yt-dlp not installed")
            return None
        except Exception as e:
            logger.warning("yt-dlp subtitle download failed: %s", e)
            return None

    @staticmethod
    def _whisper_fallback(youtube_url: str) -> str:
        """Download audio from YouTube and transcribe with Whisper."""
        import yt_dlp

        tmp_dir = tempfile.mkdtemp(prefix="yt_audio_")
        audio_path = os.path.join(tmp_dir, "audio.mp3")

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio",
            "outtmpl": os.path.join(tmp_dir, "audio.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Find the downloaded audio file
        audio_files = list(Path(tmp_dir).glob("audio.*"))
        if not audio_files:
            raise ValueError("YouTube 音訊下載失敗")

        audio_file = str(audio_files[0])

        # Use AudioVideoExtractor for Whisper transcription
        from app.services.media_extractors.audio_video_extractor import AudioVideoExtractor
        av_extractor = AudioVideoExtractor()
        result = av_extractor.extract(audio_file, resource_name="YouTube Audio")

        # Cleanup
        try:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

        return result.raw_text


def _parse_vtt(raw: str) -> str:
    """Parse VTT/SRT subtitle to timestamped transcript, removing duplicates."""
    import re

    lines = raw.split("\n")
    entries: list[tuple[str, str]] = []
    current_time = ""
    current_text_parts: list[str] = []

    for line in lines:
        line = line.strip()

        # Skip VTT header and empty lines
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue

        # Timestamp line (VTT format: 00:00:00.000 --> 00:00:05.000)
        ts_match = re.match(r'(\d{1,2}:\d{2}:\d{2})[.\d]*\s*-->', line)
        if ts_match:
            # Flush previous entry
            if current_time and current_text_parts:
                text = " ".join(current_text_parts).strip()
                # Remove VTT tags like <c>, </c>, etc.
                text = re.sub(r'<[^>]+>', '', text)
                if text:
                    entries.append((current_time, text))

            current_time = ts_match.group(1)
            current_text_parts = []
            continue

        # Skip pure numeric lines (SRT sequence numbers)
        if re.match(r'^\d+$', line):
            continue

        # Text content
        if line:
            current_text_parts.append(line)

    # Flush last entry
    if current_time and current_text_parts:
        text = " ".join(current_text_parts).strip()
        text = re.sub(r'<[^>]+>', '', text)
        if text:
            entries.append((current_time, text))

    # Deduplicate consecutive identical texts (common in auto-subs)
    deduped: list[str] = []
    prev_text = ""
    for timestamp, text in entries:
        if text != prev_text:
            deduped.append(f"[{timestamp}] {text}")
            prev_text = text

    return "\n".join(deduped)
