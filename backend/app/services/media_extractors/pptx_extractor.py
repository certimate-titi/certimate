"""PPTX extractor — python-pptx for .pptx files."""

from __future__ import annotations

import logging
from pathlib import Path

from app.services.media_extractors.base import ExtractionResult

logger = logging.getLogger(__name__)


class PptxExtractor:

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        from pptx import Presentation

        prs = Presentation(file_path)
        parts: list[str] = []
        sections: list[dict] = []

        for slide_num, slide in enumerate(prs.slides, 1):
            slide_texts: list[str] = []
            slide_title = f"投影片 {slide_num}"
            notes_text = ""

            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = para.text.strip()
                        if text:
                            slide_texts.append(text)

                # Extract table content
                if shape.has_table:
                    table = shape.table
                    for row in table.rows:
                        cells = [cell.text.strip() for cell in row.cells]
                        slide_texts.append(" | ".join(cells))

            # Extract title from first text shape or slide layout
            if slide.shapes.title and slide.shapes.title.text.strip():
                slide_title = slide.shapes.title.text.strip()

            # Extract speaker notes
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes_text = slide.notes_slide.notes_text_frame.text.strip()

            slide_content = "\n".join(slide_texts)
            if notes_text:
                slide_content += f"\n\n> 備忘稿：{notes_text}"

            if slide_content.strip():
                parts.append(f"## {slide_title}\n{slide_content}")
                sections.append({
                    "title": slide_title,
                    "content": slide_content,
                    "page_start": slide_num,
                    "page_end": slide_num,
                    "depth": 1,
                })

        raw_text = "\n\n".join(parts)

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type="pptx",
            raw_text=raw_text,
            metadata=f"slides:{len(sections)}",
            sections=sections,
        )
