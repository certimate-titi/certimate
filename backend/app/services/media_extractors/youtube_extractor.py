"""YouTube extractor — 雙路徑分流。

有 CC 字幕 → yt-dlp 下載 VTT → Gemini 2.5 Flash text K-06 結構化
無 CC 字幕 → Gemini 2.5 Pro 直餵 YouTube URL（File API）

yt-dlp 只用於 metadata probe（download=False）與 VTT 下載，不需 ffmpeg。
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)

_GEMINI_MODEL_PRO = "gemini-2.5-pro"
_GEMINI_MODEL_FLASH = "gemini-2.5-flash"

# VTT CC path — Gemini Flash 結構化 prompt
_CC_STRUCTURING_PROMPT = """請根據以下 YouTube 字幕文字，產出結構化學習內容（JSON 格式）：

{
  "title": "影片標題",
  "transcript": "完整逐字稿，每段前加時間戳，格式：[HH:MM:SS] 內容",
  "sections": [
    {"timestamp": "00:00:00", "title": "章節標題", "summary": "章節摘要"}
  ]
}

字幕原文：
{vtt_text}

要求：
1. 只回傳 JSON，不加任何說明文字
2. transcript：根據字幕整理成連貫逐字稿
3. sections：依主題劃分章節
"""

# No-CC path — Gemini Pro direct YouTube URL prompt
_DIRECT_TRANSCRIPT_PROMPT = """請分析這段 YouTube 影片並產出以下內容（JSON 格式）：

{
  "title": "影片標題",
  "transcript": "逐字稿，每行前加時間戳，格式：[HH:MM:SS] 內容",
  "sections": [
    {"timestamp": "00:00:00", "title": "章節標題", "summary": "章節摘要"}
  ]
}

要求：
1. title：影片標題（優先取影片自身標題）
2. transcript：完整時間戳逐字稿，繁體中文優先，若原為英文則保持英文
3. sections：依主題劃分章節，每個章節含時間戳、標題與摘要
4. 只回傳 JSON，不加任何說明文字
"""


@dataclass
class YouTubeMetadata:
    """yt-dlp metadata probe 結果。"""

    duration_seconds: float
    has_cc: bool  # subtitles 或 automatic_captions 任一非空
    title: str = ""


def probe_youtube_metadata(youtube_url: str) -> YouTubeMetadata:
    """使用 yt-dlp（download=False）取得 metadata + CC 可用性。

    不下載 audio / video，僅取 info dict。
    若 yt-dlp 不可用則回傳 duration_seconds=0, has_cc=False（fallback）。
    """
    try:
        import yt_dlp  # type: ignore[import]
    except ImportError:
        logger.warning("yt-dlp 未安裝，無法取得 YouTube metadata；has_cc=False fallback")
        return YouTubeMetadata(duration_seconds=0, has_cc=False)

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
    except Exception as exc:
        logger.warning("yt-dlp probe 失敗: %s", exc)
        return YouTubeMetadata(duration_seconds=0, has_cc=False)

    duration = float(info.get("duration") or 0)
    title = info.get("title") or ""

    # subtitles = 手動 CC；automatic_captions = 自動 CC
    subtitles = info.get("subtitles") or {}
    auto_captions = info.get("automatic_captions") or {}
    has_cc = bool(subtitles or auto_captions)

    return YouTubeMetadata(duration_seconds=duration, has_cc=has_cc, title=title)


_PREFERRED_LANGS = ["zh-TW", "zh-Hant", "zh-CN", "zh-Hans", "zh", "en"]


def _extract_video_id(youtube_url: str) -> str | None:
    """從 YouTube URL 抽 video_id（11 字英數+_- 串）。"""
    import re

    # 涵蓋 watch?v=ID / youtu.be/ID / shorts/ID / embed/ID / live/ID
    m = re.search(
        r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})",
        youtube_url,
    )
    return m.group(1) if m else None


def _download_transcript_via_api(youtube_url: str) -> str | None:
    """主路徑：用 youtube-transcript-api 抽字幕。

    走 player timedtext endpoint（非 yt-dlp 的 IP rate-limited 端點），
    多用戶 scaling 時 429 風險顯著降低。失敗回 None 讓上層 fallback。

    回傳：純文字（已 join，去時間碼），可直接餵 K-01 結構化。
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore[import]
        from youtube_transcript_api._errors import (  # type: ignore[import]
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )
    except ImportError:
        logger.warning("youtube-transcript-api 未安裝，fallback 到 yt-dlp")
        return None

    video_id = _extract_video_id(youtube_url)
    if not video_id:
        logger.warning("無法從 URL 抽 video_id: %s", youtube_url)
        return None

    try:
        api = YouTubeTranscriptApi()
        # fetch() 自動嘗試所有 preferred langs，找到第一個可用就回
        fetched = api.fetch(video_id, languages=_PREFERRED_LANGS)
    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        logger.info("transcript-api 無字幕（video=%s）: %s", video_id, exc)
        return None
    except VideoUnavailable as exc:
        logger.warning("transcript-api 影片不可用: %s", exc)
        return None
    except Exception as exc:  # 含 429 / IP block / proxy error
        logger.warning(
            "transcript-api 失敗（fallback yt-dlp）: %s",
            exc,
        )
        return None

    # FetchedTranscript supports iter → FetchedTranscriptSnippet(text, start, duration)
    pieces = [s.text.strip() for s in fetched if getattr(s, "text", "").strip()]
    if not pieces:
        return None

    # 用 _parse_vtt 級別的去重邏輯，再 join
    seen: set[str] = set()
    unique: list[str] = []
    for p in pieces:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return " ".join(unique)


def _download_vtt(youtube_url: str, tmpdir: str) -> str | None:
    """yt-dlp fallback：下載最佳 CC 字幕到 tmpdir，回傳 VTT 文字內容（或 None）。

    遇 YouTube 429 throttle 走 exponential backoff retry（最多 3 次）。
    主路徑 _download_transcript_via_api 失敗才會進來。
    """
    import time as _time

    try:
        import yt_dlp  # type: ignore[import]
    except ImportError:
        return None

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        # YouTube subtitle 語言碼差異：TED 用 zh-TW，部分平台用 zh-Hant，
        # 大陸用 zh-CN/zh-Hans，未指定地區用 zh。fallback 到 en。
        "subtitleslangs": ["zh-TW", "zh-Hant", "zh-CN", "zh-Hans", "zh", "en"],
        "subtitlesformat": "vtt",
        "outtmpl": os.path.join(tmpdir, "sub"),
        "no_warnings": True,
    }

    # Retry：429 throttle 用 exponential backoff
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            break  # success
        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            if "429" in msg or "too many requests" in msg:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.warning(
                    "yt-dlp 429 throttle (attempt %d/3), wait %ds: %s",
                    attempt + 1, wait, exc,
                )
                _time.sleep(wait)
                continue
            # 非 429 失敗直接放棄
            logger.warning("yt-dlp VTT 下載失敗（非 429）: %s", exc)
            return None
    else:
        logger.warning("yt-dlp 429 retry 耗盡，放棄 VTT 下載: %s", last_exc)
        return None

    # 尋找第一個 .vtt 檔
    for fname in os.listdir(tmpdir):
        if fname.endswith(".vtt"):
            fpath = os.path.join(tmpdir, fname)
            with open(fpath, encoding="utf-8", errors="replace") as f:
                return f.read()
    return None


def _parse_vtt(vtt_text: str) -> str:
    """將 VTT 字幕文字轉成連貫文字（去除時間碼行、WEBVTT 標頭、重複行）。"""
    import re

    lines = vtt_text.splitlines()
    result: list[str] = []
    seen: set[str] = set()

    for line in lines:
        line = line.strip()
        # 跳過空行、WEBVTT 標頭、NOTE、時間碼行
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ", line):
            continue
        if re.match(r"^\d+$", line):
            continue
        # 去重（自動字幕常有重複）
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)

    return " ".join(result)


def _apply_k01_structuring(vtt_text: str, title: str, youtube_url: str) -> ExtractionResult:
    """用 Gemini 2.5 Flash 將 VTT 文字結構化為 K-06 格式。"""
    import json

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise ValueError(f"google-genai SDK 未安裝: {exc}") from exc

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 未設定")

    client = genai.Client(api_key=api_key)

    plain_text = _parse_vtt(vtt_text)
    prompt = _CC_STRUCTURING_PROMPT.replace("{vtt_text}", plain_text[:50000])

    try:
        response = client.models.generate_content(
            model=_GEMINI_MODEL_FLASH,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=8192,
                temperature=0.1,
            ),
        )
    except Exception as exc:
        raise ValueError(f"Gemini Flash 結構化失敗: {exc}") from exc

    raw_output = response.text or ""
    return _parse_gemini_json(raw_output, fallback_title=title, youtube_url=youtube_url, model=_GEMINI_MODEL_FLASH)


def _gemini_direct_extract(youtube_url: str, resource_name: str = "") -> ExtractionResult:
    """Gemini 2.5 Pro 直餵 YouTube URL（無 CC 路徑）。"""
    import json

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise ValueError(f"google-genai SDK 未安裝: {exc}") from exc

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 未設定")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=_GEMINI_MODEL_PRO,
            contents=[
                types.Part(file_data=types.FileData(file_uri=youtube_url)),
                _DIRECT_TRANSCRIPT_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=8192,
                temperature=0.1,
            ),
        )
    except Exception as exc:
        err_msg = str(exc).lower()
        if "private" in err_msg or "unavailable" in err_msg:
            raise ValueError(f"無法存取此 YouTube 影片（可能為私人影片或地區限制）: {exc}") from exc
        if "too long" in err_msg or "duration" in err_msg:
            raise ValueError(f"YouTube 影片過長，超出 Gemini 處理上限: {exc}") from exc
        if "safety" in err_msg or "policy" in err_msg or "terms" in err_msg:
            raise ValueError(f"YouTube 影片違反內容政策，無法處理: {exc}") from exc
        raise ValueError(f"Gemini 處理 YouTube 影片失敗: {exc}") from exc

    raw_output = response.text or ""
    return _parse_gemini_json(raw_output, fallback_title=resource_name or youtube_url, youtube_url=youtube_url, model=_GEMINI_MODEL_PRO)


def _parse_gemini_json(
    raw_output: str,
    fallback_title: str,
    youtube_url: str,
    model: str,
) -> ExtractionResult:
    """解析 Gemini JSON 輸出，回傳 ExtractionResult。"""
    import json

    title = fallback_title
    raw_text = raw_output
    sections: list[dict] = []

    try:
        clean = raw_output.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])
        data = json.loads(clean)
        title = data.get("title") or fallback_title
        raw_text = data.get("transcript") or raw_output
        sections = data.get("sections") or []
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Gemini 回應無法解析為 JSON，使用原始文字; url=%s", youtube_url)

    logger.info("YouTube 逐字稿已擷取 (%d chars); model=%s url=%s", len(raw_text), model, youtube_url)

    return ExtractionResult(
        title=title,
        content_type="transcript",
        raw_text=raw_text,
        metadata=f"source:youtube,model:{model},url:{youtube_url}",
        sections=sections,
    )


class YouTubeExtractor:
    """YouTube 雙路徑擷取器。

    有 CC → VTT + Gemini Flash 結構化
    無 CC → Gemini Pro 直餵 YouTube URL
    """

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        """file_path 為 YouTube URL。

        路徑選擇由 probe_youtube_metadata 決定；
        測試時可直接呼叫 _extract_with_cc 或 _extract_without_cc。
        """
        youtube_url = file_path
        try:
            meta = probe_youtube_metadata(youtube_url)
        except Exception as exc:
            logger.warning("YouTube metadata probe 失敗，走無 CC 路徑: %s", exc)
            meta = YouTubeMetadata(duration_seconds=0, has_cc=False)

        if meta.has_cc:
            return self._extract_with_cc(youtube_url, resource_name or meta.title)
        else:
            return _gemini_direct_extract(youtube_url, resource_name or meta.title)

    def _extract_with_cc(self, youtube_url: str, resource_name: str = "") -> ExtractionResult:
        """有 CC 路徑：
        1. 主路徑 youtube-transcript-api（player endpoint，配額寬鬆）→ 已是純文字
        2. fallback 1 yt-dlp VTT（429 風險高，仍保留作後盾）
        3. fallback 2 Gemini Pro 直餵（成本最高）→ Flash 結構化
        """
        # 主路徑：transcript-api 直回純文字（無 VTT 中介）
        transcript_text = _download_transcript_via_api(youtube_url)
        if transcript_text:
            logger.info(
                "[yt-cc] transcript-api 成功，text_len=%d url=%s",
                len(transcript_text), youtube_url,
            )
            # _apply_k01_structuring 內部會 _parse_vtt — 對純文字無害（無時間碼行可剝）
            # 但為了避免 50KB 截斷處時間語意被切，這裡直接組成單行 VTT-like 文字
            return _apply_k01_structuring(
                transcript_text, title=resource_name, youtube_url=youtube_url,
            )

        # fallback 1：yt-dlp VTT（IP 429 風險）
        with tempfile.TemporaryDirectory() as tmpdir:
            vtt_text = _download_vtt(youtube_url, tmpdir)
        if vtt_text:
            logger.info("[yt-cc] yt-dlp VTT fallback 成功 url=%s", youtube_url)
            return _apply_k01_structuring(vtt_text, title=resource_name, youtube_url=youtube_url)

        # fallback 2：Gemini Pro 直餵（最貴）
        logger.warning("VTT 雙路徑均失敗，fallback 到 Gemini Pro 直餵; url=%s", youtube_url)
        return _gemini_direct_extract(youtube_url, resource_name)
