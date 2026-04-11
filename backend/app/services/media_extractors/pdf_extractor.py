"""PDF extractor — pymupdf text layer, Claude Vision fallback for scanned PDFs."""

from __future__ import annotations

import logging
from pathlib import Path

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)


class PdfExtractor:

    def __init__(self, claude_service=None):
        self.claude = claude_service

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        pdf_bytes = Path(file_path).read_bytes()

        # Try local extraction first (pymupdf)
        pages = self._extract_with_pymupdf(pdf_bytes)

        # Fallback: Claude Vision for scanned PDFs
        if not pages and self.claude:
            pages = self._extract_with_vision(pdf_bytes)

        if not pages:
            raise ValueError("無法解析 PDF 文件（文字層和 Vision OCR 均失敗）")

        raw_text = "\n\n".join(
            f"--- 第 {p['page_num']} 頁 ---\n{p['content']}" for p in pages
        )
        metadata = f"pages:{len(pages)}"

        sections = [
            {
                "title": f"p.{p['page_num']}",
                "content": p["content"],
                "page_start": p["page_num"],
                "page_end": p["page_num"],
                "depth": 1,
            }
            for p in pages
        ]

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type="pdf",
            raw_text=raw_text,
            metadata=metadata,
            sections=sections,
        )

    @staticmethod
    def _extract_with_pymupdf(pdf_bytes: bytes) -> list[dict]:
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages = []
            for i in range(len(doc)):
                text = doc[i].get_text()
                if text.strip():
                    pages.append({"page_num": i + 1, "content": text.strip()})
            doc.close()
            return pages
        except Exception as e:
            logger.warning("pymupdf extraction failed: %s", e)
            return []

    def _extract_with_vision(self, pdf_bytes: bytes) -> list[dict]:
        try:
            raw = self.claude.parse_pdf(pdf_bytes, "請分析此 PDF 並以純文字回傳所有內容。")
            if raw and raw.strip():
                return [{"page_num": 1, "content": raw.strip()}]
        except Exception as e:
            logger.warning("Claude Vision PDF fallback failed: %s", e)
        return []
