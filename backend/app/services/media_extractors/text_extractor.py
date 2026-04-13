"""Text/Markdown extractor — plain text file reading."""

from __future__ import annotations

from pathlib import Path

from app.services.media_extractors.base import ExtractionResult


class TextExtractor:

    def extract(self, file_path: str, resource_name: str = "") -> ExtractionResult:
        content = Path(file_path).read_text(encoding="utf-8")

        sections: list[dict] = []
        current_title = resource_name or Path(file_path).stem
        current_depth = 1
        current_content: list[str] = []

        for line in content.split("\n"):
            if line.startswith("### "):
                if current_content:
                    sections.append({
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                        "page_start": None, "page_end": None,
                        "depth": current_depth,
                    })
                current_title = line.lstrip("# ").strip()
                current_depth = 3
                current_content = []
            elif line.startswith("## "):
                if current_content:
                    sections.append({
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                        "page_start": None, "page_end": None,
                        "depth": current_depth,
                    })
                current_title = line.lstrip("# ").strip()
                current_depth = 2
                current_content = []
            elif line.startswith("# "):
                if current_content:
                    sections.append({
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                        "page_start": None, "page_end": None,
                        "depth": current_depth,
                    })
                current_title = line.lstrip("# ").strip()
                current_depth = 1
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append({
                "title": current_title,
                "content": "\n".join(current_content).strip(),
                "page_start": None, "page_end": None,
                "depth": current_depth,
            })

        return ExtractionResult(
            title=resource_name or Path(file_path).stem,
            content_type="markdown" if file_path.endswith(".md") else "txt",
            raw_text=content,
            metadata="",
            sections=sections,
        )
