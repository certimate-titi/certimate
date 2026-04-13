"""Base class for all media extractors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ExtractionResult:
    """Layer 1 extraction output — fed to K-01 for Markdown structuring."""

    title: str
    content_type: str          # pdf|docx|pptx|xlsx|doc|ppt|xls|image_ocr|transcript
    raw_text: str              # 提取的原始文字（可能很長）
    metadata: str = ""         # 來源元資料
    sections: list[dict] = field(default_factory=list)  # 可選的預分段


class MediaExtractor(Protocol):
    """Protocol for all media extractors."""

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        """Extract raw text from the given file."""
        ...
