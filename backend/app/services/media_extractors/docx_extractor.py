"""DOCX extractor — python-docx for .docx files."""

from __future__ import annotations

import logging
from pathlib import Path

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)


class DocxExtractor:

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        from docx import Document

        doc = Document(file_path)
        parts: list[str] = []
        sections: list[dict] = []
        current_title = resource_name or Path(file_path).stem
        current_content: list[str] = []
        current_depth = 1
        section_idx = 0

        for para in doc.paragraphs:
            style_name = (para.style.name or "").lower()
            text = para.text.strip()
            if not text:
                current_content.append("")
                continue

            # Detect heading levels
            if style_name.startswith("heading"):
                # Flush current section
                if current_content:
                    content = "\n".join(current_content).strip()
                    if content:
                        sections.append({
                            "title": current_title,
                            "content": content,
                            "page_start": None,
                            "page_end": None,
                            "depth": current_depth,
                        })
                        section_idx += 1

                # Parse heading level (Heading 1 → depth 1, etc.)
                try:
                    level = int(style_name.replace("heading", "").strip())
                except ValueError:
                    level = 1
                current_title = text
                current_depth = min(level, 3)
                current_content = []
            else:
                current_content.append(text)

            parts.append(text)

        # Flush last section
        if current_content:
            content = "\n".join(current_content).strip()
            if content:
                sections.append({
                    "title": current_title,
                    "content": content,
                    "page_start": None,
                    "page_end": None,
                    "depth": current_depth,
                })

        # Also extract tables
        for i, table in enumerate(doc.tables):
            rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                rows.append(" | ".join(cells))
            table_text = "\n".join(rows)
            if table_text.strip():
                parts.append(f"\n[表格 {i + 1}]\n{table_text}")

        raw_text = "\n".join(parts)

        # If no sections detected (no headings), create one big section
        if not sections:
            sections = [{
                "title": resource_name or Path(file_path).stem,
                "content": raw_text,
                "page_start": None,
                "page_end": None,
                "depth": 1,
            }]

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type="docx",
            raw_text=raw_text,
            metadata="",
            sections=sections,
        )
