"""Audio/Video extractor — OpenAI Whisper API for transcription.

Handles:
- Audio files (mp3, wav, m4a, flac, ogg, wma)
- Video files (mp4, mov, avi, mkv, webm)
- YouTube URLs (yt-dlp subtitles → Whisper fallback)

Long files (>20 min) are auto-split using ffmpeg.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)

# Whisper API 單次上限 25MB，保守切 20 分鐘
SEGMENT_DURATION_SECS = 20 * 60  # 20 minutes
WHISPER_MODEL = "whisper-1"

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".wma", ".aac"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv"}


class AudioVideoExtractor:
    """Extracts transcripts from audio/video files using OpenAI Whisper API."""

    def __init__(self):
        self._openai_client = None

    def _get_openai(self):
        if self._openai_client is None:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                from app.core.config import get_settings
                api_key = get_settings().OPENAI_API_KEY or ""
            if not api_key:
                raise ValueError("音訊/影片轉錄需要設定 OPENAI_API_KEY（Whisper API）")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        ext = Path(file_path).suffix.lower()

        if ext in VIDEO_EXTENSIONS:
            # Step 1: Extract audio track from video
            audio_path = self._extract_audio_from_video(file_path)
            content_type = "transcript"
            metadata_format = f"video:{ext.lstrip('.')}"
        elif ext in AUDIO_EXTENSIONS:
            audio_path = file_path
            content_type = "transcript"
            metadata_format = f"audio:{ext.lstrip('.')}"
        else:
            raise ValueError(f"不支援的音訊/影片格式: {ext}")

        # Step 2: Check duration and split if needed
        duration = self._get_duration(audio_path)
        logger.info("Audio duration: %.0f seconds (%.1f minutes)", duration, duration / 60)

        if duration > SEGMENT_DURATION_SECS:
            segments = self._split_audio(audio_path, SEGMENT_DURATION_SECS)
        else:
            segments = [audio_path]

        # Step 3: Transcribe each segment
        transcripts: list[str] = []
        for i, seg_path in enumerate(segments):
            offset_secs = i * SEGMENT_DURATION_SECS
            transcript = self._transcribe_segment(seg_path, offset_secs)
            transcripts.append(transcript)

            # Clean up temporary segment files
            if seg_path != audio_path and seg_path != file_path:
                try:
                    os.remove(seg_path)
                except Exception:
                    pass

        # Clean up extracted audio from video
        if audio_path != file_path:
            try:
                os.remove(audio_path)
            except Exception:
                pass

        raw_text = "\n\n".join(transcripts)
        total_minutes = int(duration / 60)
        metadata = f"{metadata_format},duration:{total_minutes}m,segments:{len(segments)}"

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type=content_type,
            raw_text=raw_text,
            metadata=metadata,
        )

    def _extract_audio_from_video(self, video_path: str) -> str:
        """Use ffmpeg to extract audio track as mp3."""
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "libmp3lame", "-q:a", "4",
            "-y", tmp_audio,
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=300)
            return tmp_audio
        except FileNotFoundError:
            raise ValueError("需要安裝 ffmpeg 才能處理影片檔案")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"ffmpeg 音軌提取失敗: {e.stderr.decode()[:200]}")

    @staticmethod
    def _get_duration(audio_path: str) -> float:
        """Get audio duration in seconds using ffprobe."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
            # If ffprobe not available, estimate from file size
            # ~128kbps → ~16KB/sec
            file_size = Path(audio_path).stat().st_size
            return file_size / 16000

    @staticmethod
    def _split_audio(audio_path: str, segment_secs: int) -> list[str]:
        """Split audio into segments using ffmpeg."""
        tmp_dir = tempfile.mkdtemp(prefix="whisper_segments_")
        pattern = os.path.join(tmp_dir, "seg_%03d.mp3")

        cmd = [
            "ffmpeg", "-i", audio_path,
            "-f", "segment", "-segment_time", str(segment_secs),
            "-acodec", "libmp3lame", "-q:a", "4",
            "-y", pattern,
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=600)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"ffmpeg 音訊切割失敗: {e.stderr.decode()[:200]}")

        segments = sorted(Path(tmp_dir).glob("seg_*.mp3"))
        return [str(s) for s in segments]

    def _transcribe_segment(self, audio_path: str, offset_secs: int = 0) -> str:
        """Transcribe a single audio segment using OpenAI Whisper API."""
        client = self._get_openai()

        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=f,
                response_format="verbose_json",
                language="zh",
            )

        # Build timestamped transcript
        lines: list[str] = []
        if hasattr(response, "segments") and response.segments:
            for seg in response.segments:
                start = seg.get("start", 0) if isinstance(seg, dict) else getattr(seg, "start", 0)
                text = seg.get("text", "") if isinstance(seg, dict) else getattr(seg, "text", "")
                abs_start = start + offset_secs
                timestamp = self._format_timestamp(abs_start)
                lines.append(f"[{timestamp}] {text.strip()}")
        else:
            # Fallback: plain text
            text = response.text if hasattr(response, "text") else str(response)
            timestamp = self._format_timestamp(offset_secs)
            lines.append(f"[{timestamp}] {text.strip()}")

        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds as HH:MM:SS."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
