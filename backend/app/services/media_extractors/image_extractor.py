"""Image extractor — Claude Vision OCR."""

from __future__ import annotations

import logging
from pathlib import Path

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)

IMAGE_MEDIA_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
}


class ImageExtractor:

    def __init__(self, claude_service=None, ocr_prompt: str | None = None):
        self.claude = claude_service
        self.ocr_prompt = ocr_prompt or (
            "請辨識這張圖片中的所有文字內容，並以結構化方式輸出。"
            "要求：1. 完整辨識所有可見文字 2. 保留段落結構 "
            "3. 表格轉 Markdown 4. 數學公式保留原始表達\n"
            "以純文字格式回傳辨識結果。"
        )

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        if not self.claude:
            raise ValueError("圖片 OCR 需要設定 ANTHROPIC_API_KEY")

        image_bytes = Path(file_path).read_bytes()
        ext = Path(file_path).suffix.lower()
        media_type = IMAGE_MEDIA_TYPES.get(ext, "image/png")

        text = self.claude.parse_image(image_bytes, media_type, self.ocr_prompt)

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type="image_ocr",
            raw_text=text or "",
            metadata=f"format:{ext.lstrip('.')}",
        )
