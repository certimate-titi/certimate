"""Extractor registry — dispatches to the correct extractor by resource type."""

from __future__ import annotations

import logging

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)

# Extension → resource_type mapping
EXTENSION_TO_TYPE = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".pptx": "pptx",
    ".xlsx": "xlsx",
    ".doc": "doc",
    ".ppt": "ppt",
    ".xls": "xls",
    ".md": "markdown",
    ".txt": "txt",
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".gif": "image", ".webp": "image", ".bmp": "image",
    ".mp3": "audio", ".wav": "audio", ".m4a": "audio",
    ".flac": "audio", ".ogg": "audio", ".wma": "audio", ".aac": "audio",
    ".mp4": "video", ".mov": "video", ".avi": "video",
    ".mkv": "video", ".webm": "video", ".wmv": "video", ".flv": "video",
}


def get_extractor(resource_type: str, *, claude_service=None, ocr_prompt: str | None = None):
    """Get the appropriate extractor instance for the given resource type."""

    if resource_type == "pdf":
        from app.services.media_extractors.pdf_extractor import PdfExtractor
        return PdfExtractor(claude_service=claude_service)

    elif resource_type == "docx":
        from app.services.media_extractors.docx_extractor import DocxExtractor
        return DocxExtractor()

    elif resource_type == "pptx":
        from app.services.media_extractors.pptx_extractor import PptxExtractor
        return PptxExtractor()

    elif resource_type == "xlsx":
        from app.services.media_extractors.xlsx_extractor import XlsxExtractor
        return XlsxExtractor()

    elif resource_type in ("doc", "ppt", "xls"):
        from app.services.media_extractors.legacy_office_extractor import LegacyOfficeExtractor
        return LegacyOfficeExtractor()

    elif resource_type == "image":
        from app.services.media_extractors.image_extractor import ImageExtractor
        return ImageExtractor(claude_service=claude_service, ocr_prompt=ocr_prompt)

    elif resource_type in ("audio", "video"):
        from app.services.media_extractors.audio_video_extractor import AudioVideoExtractor
        return AudioVideoExtractor()

    elif resource_type == "youtube":
        from app.services.media_extractors.youtube_extractor import YouTubeExtractor
        return YouTubeExtractor()

    elif resource_type in ("markdown", "txt"):
        from app.services.media_extractors.text_extractor import TextExtractor
        return TextExtractor()

    else:
        raise ValueError(f"不支援的資源類型: {resource_type}")


def extract(
    resource_type: str,
    file_path: str,
    resource_name: str = "",
    *,
    claude_service=None,
    ocr_prompt: str | None = None,
) -> ExtractionResult:
    """Convenience function: get extractor and extract in one call."""
    extractor = get_extractor(
        resource_type,
        claude_service=claude_service,
        ocr_prompt=ocr_prompt,
    )
    return extractor.extract(file_path, resource_name)
