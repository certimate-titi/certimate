"""YouTube extractor — Gemini File API 直接處理 YouTube URL。

完全移除 yt-dlp / Whisper / ffmpeg 依賴。
Gemini 2.5 Pro 支援以 FileData(file_uri=youtube_url) 直接輸入 YouTube 連結，
產出時間戳逐字稿與章節結構。
"""

from __future__ import annotations

import logging
import os

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)

_GEMINI_MODEL = "gemini-2.5-pro"

_TRANSCRIPT_PROMPT = """請分析這段 YouTube 影片並產出以下內容（JSON 格式）：

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


class YouTubeExtractor:
    """用 Gemini File API 直接從 YouTube URL 擷取逐字稿與章節結構。

    不依賴 yt-dlp、Whisper 或 ffmpeg。
    """

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        """file_path 為 YouTube URL。"""
        youtube_url = file_path
        return self._gemini_extract(youtube_url, resource_name)

    @staticmethod
    def _gemini_extract(youtube_url: str, resource_name: str = "") -> ExtractionResult:
        """呼叫 Gemini File API 直接處理 YouTube URL。"""
        import json

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ValueError(
                f"google-genai SDK 未安裝，無法處理 YouTube 影片: {exc}"
            ) from exc

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 未設定，無法呼叫 Gemini API")

        client = genai.Client(api_key=api_key)

        try:
            response = client.models.generate_content(
                model=_GEMINI_MODEL,
                contents=[
                    types.Part(
                        file_data=types.FileData(file_uri=youtube_url)
                    ),
                    _TRANSCRIPT_PROMPT,
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
                raise ValueError(
                    f"無法存取此 YouTube 影片（可能為私人影片或地區限制）: {exc}"
                ) from exc
            if "too long" in err_msg or "duration" in err_msg:
                raise ValueError(
                    f"YouTube 影片過長，超出 Gemini 處理上限: {exc}"
                ) from exc
            if "safety" in err_msg or "policy" in err_msg or "terms" in err_msg:
                raise ValueError(
                    f"YouTube 影片違反內容政策，無法處理: {exc}"
                ) from exc
            raise ValueError(
                f"Gemini 處理 YouTube 影片失敗: {exc}"
            ) from exc

        raw_output = response.text or ""

        # 解析 JSON 輸出
        title = resource_name or youtube_url
        raw_text = raw_output
        sections: list[dict] = []

        try:
            # 移除可能的 markdown code fence
            clean = raw_output.strip()
            if clean.startswith("```"):
                lines = clean.split("\n")
                clean = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])

            data = json.loads(clean)
            title = data.get("title") or resource_name or youtube_url
            raw_text = data.get("transcript") or raw_output
            sections = data.get("sections") or []
        except (json.JSONDecodeError, AttributeError):
            logger.warning(
                "Gemini 回應無法解析為 JSON，使用原始文字; url=%s", youtube_url
            )

        logger.info(
            "YouTube 逐字稿已由 Gemini 擷取 (%d chars); url=%s", len(raw_text), youtube_url
        )

        return ExtractionResult(
            title=title,
            content_type="transcript",
            raw_text=raw_text,
            metadata=f"source:youtube_gemini,model:{_GEMINI_MODEL},url:{youtube_url}",
            sections=sections,
        )
