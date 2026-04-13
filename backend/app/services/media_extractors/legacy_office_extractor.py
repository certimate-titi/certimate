"""Legacy Office extractor — DOC/PPT/XLS (OLE format) using olefile + pure Python."""

from __future__ import annotations

import logging
import struct
from pathlib import Path

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)


class LegacyOfficeExtractor:
    """Handles .doc, .ppt, .xls using olefile for basic text extraction."""

    SUPPORTED_TYPES = {"doc", "ppt", "xls"}

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        ext = Path(file_path).suffix.lower().lstrip(".")
        if ext not in self.SUPPORTED_TYPES:
            raise ValueError(f"不支援的舊版 Office 格式: {ext}")

        if ext == "doc":
            return self._extract_doc(file_path, resource_name)
        elif ext == "ppt":
            return self._extract_ppt(file_path, resource_name)
        elif ext == "xls":
            return self._extract_xls(file_path, resource_name)

        raise ValueError(f"不支援的格式: {ext}")

    def _extract_doc(self, file_path: str, resource_name: str) -> ExtractionResult:
        """Extract text from .doc using olefile (WordDocument stream)."""
        import olefile

        text_parts: list[str] = []
        try:
            ole = olefile.OleFileIO(file_path)
            if ole.exists("WordDocument"):
                # Try to extract from the WordDocument stream
                # This is a simplified extraction — complex formatting is lost
                word_stream = ole.openstream("WordDocument").read()
                text = self._decode_word_stream(word_stream)
                if text:
                    text_parts.append(text)

            # Also try the "1Table" or "0Table" stream for additional text
            for stream_name in ["1Table", "0Table"]:
                if ole.exists(stream_name):
                    try:
                        data = ole.openstream(stream_name).read()
                        decoded = data.decode("utf-8", errors="ignore")
                        # Filter printable characters
                        cleaned = "".join(c for c in decoded if c.isprintable() or c in "\n\t")
                        if len(cleaned) > 50:
                            text_parts.append(cleaned)
                    except Exception:
                        pass

            ole.close()
        except Exception as e:
            logger.warning("DOC extraction via olefile failed: %s", e)

        if not text_parts:
            # Last resort: raw binary text extraction
            text_parts = [self._raw_text_extract(file_path)]

        raw_text = "\n".join(text_parts).strip()
        if not raw_text:
            raise ValueError("無法從 .doc 檔案提取文字內容")

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type="doc",
            raw_text=raw_text,
            metadata="format:legacy_doc",
        )

    def _extract_ppt(self, file_path: str, resource_name: str) -> ExtractionResult:
        """Extract text from .ppt using olefile."""
        import olefile

        text_parts: list[str] = []
        try:
            ole = olefile.OleFileIO(file_path)
            # PPT text is typically in "PowerPoint Document" stream
            if ole.exists("PowerPoint Document"):
                data = ole.openstream("PowerPoint Document").read()
                text = self._extract_ppt_text_records(data)
                if text:
                    text_parts.append(text)
            ole.close()
        except Exception as e:
            logger.warning("PPT extraction via olefile failed: %s", e)

        if not text_parts:
            text_parts = [self._raw_text_extract(file_path)]

        raw_text = "\n".join(text_parts).strip()
        if not raw_text:
            raise ValueError("無法從 .ppt 檔案提取文字內容")

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type="ppt",
            raw_text=raw_text,
            metadata="format:legacy_ppt",
        )

    def _extract_xls(self, file_path: str, resource_name: str) -> ExtractionResult:
        """Extract text from .xls using xlrd (if available) or raw extraction."""
        text_parts: list[str] = []

        # Try xlrd first (best for .xls)
        try:
            import xlrd
            wb = xlrd.open_workbook(file_path)
            for sheet in wb.sheets():
                rows = []
                for row_idx in range(sheet.nrows):
                    cells = [str(sheet.cell_value(row_idx, col_idx)) for col_idx in range(sheet.ncols)]
                    if any(cells):
                        rows.append(" | ".join(cells))
                if rows:
                    text_parts.append(f"## {sheet.name}\n" + "\n".join(rows))
        except ImportError:
            logger.info("xlrd not installed, using raw extraction for .xls")
            text_parts = [self._raw_text_extract(file_path)]
        except Exception as e:
            logger.warning("XLS extraction failed: %s", e)
            text_parts = [self._raw_text_extract(file_path)]

        raw_text = "\n".join(text_parts).strip()
        if not raw_text:
            raise ValueError("無法從 .xls 檔案提取文字內容")

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type="xls",
            raw_text=raw_text,
            metadata="format:legacy_xls",
        )

    @staticmethod
    def _decode_word_stream(data: bytes) -> str:
        """Try to decode WordDocument stream text."""
        # Simple approach: try UTF-16 LE decoding of text segments
        try:
            text = data.decode("utf-16-le", errors="ignore")
            # Filter to printable characters
            cleaned = "".join(c for c in text if c.isprintable() or c in "\n\t\r")
            return cleaned.strip()
        except Exception:
            return ""

    @staticmethod
    def _extract_ppt_text_records(data: bytes) -> str:
        """Extract text from PPT binary format (TextBytesAtom / TextCharsAtom records)."""
        texts: list[str] = []
        i = 0
        while i < len(data) - 8:
            try:
                rec_ver_inst = struct.unpack_from("<H", data, i)[0]
                rec_type = struct.unpack_from("<H", data, i + 2)[0]
                rec_len = struct.unpack_from("<I", data, i + 4)[0]

                # TextCharsAtom = 0x0FA0, TextBytesAtom = 0x0FA8
                if rec_type == 0x0FA0 and rec_len > 0 and rec_len < 100000:
                    text = data[i + 8:i + 8 + rec_len].decode("utf-16-le", errors="ignore")
                    text = text.strip()
                    if text and len(text) > 1:
                        texts.append(text)
                elif rec_type == 0x0FA8 and rec_len > 0 and rec_len < 100000:
                    text = data[i + 8:i + 8 + rec_len].decode("latin-1", errors="ignore")
                    text = text.strip()
                    if text and len(text) > 1:
                        texts.append(text)

                i += 8 + rec_len
            except Exception:
                i += 1

        return "\n".join(texts)

    @staticmethod
    def _raw_text_extract(file_path: str) -> str:
        """Last resort: read binary and extract printable text runs."""
        data = Path(file_path).read_bytes()
        # Try UTF-8 first
        text = data.decode("utf-8", errors="ignore")
        # Extract runs of printable characters (min 5 chars)
        import re
        runs = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\w\s,.;:!?()（）。，；：！？「」『』\-]{5,}', text)
        return "\n".join(runs)
