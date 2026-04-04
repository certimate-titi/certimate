"""DocumentProcessingService — orchestrates the full document processing pipeline.

Pipeline (per spec: 資源上傳與解析流程.md):
  1. Copyright check (scan first 2 pages for restricted keywords)
  2. Text extraction (pymupdf / pdfplumber / Claude Vision)
  3. Text cleaning (remove headers/footers/watermarks)
  4. AI structure analysis (chapters → sections → subsections)
  5. Smart chunking (by section boundaries, then token-based)
  6. Multi-level knowledge node creation
  7. Embedding (Voyage AI → pgvector)
  8. Markdown normalization & storage
  9. Original file cleanup
"""

import json
import logging
import re
import uuid
from collections import Counter
from pathlib import Path

import tiktoken
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceStatus
from app.models.resource_chunk import ResourceChunk
from app.repositories.resource_chunk_repository import ResourceChunkRepository

logger = logging.getLogger(__name__)

# --- Constants ---

IMAGE_MEDIA_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
}

COPYRIGHT_KEYWORDS = [
    "授權嚴禁轉載", "版權所有", "嚴禁翻印", "未經授權不得複製",
    "All Rights Reserved", "Confidential", "Do Not Distribute",
    "嚴禁任何形式之轉載", "禁止轉載",
]

IMAGE_OCR_PROMPT = """請辨識這張圖片中的所有文字內容，並以結構化方式輸出。
要求：1. 完整辨識所有可見文字 2. 保留段落結構 3. 表格轉 Markdown 4. 數學公式保留原始表達
以純文字格式回傳辨識結果。"""

STRUCTURE_ANALYSIS_PROMPT = (
    "分析文件結構，產出章節目錄 JSON。1-3 層深度（章→節→小節）。\n"
    "標題要簡短（15字內）。只回傳 JSON，不要 markdown。\n"
    '格式：{"chapters":[{"title":"章","page_start":1,"page_end":5,'
    '"sections":[{"title":"節","page_start":1,"page_end":2}]}]}'
)


class DocumentProcessingService:
    """Full document processing pipeline: upload → parse → chunk → embed → store."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.chunk_repo = ResourceChunkRepository(db)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Storage service for file access
        from app.services.storage_service import get_storage_service
        self.storage = get_storage_service()

        self.claude = None
        self.embedding_service = None
        self._llm = None

        if self.settings.ANTHROPIC_API_KEY:
            from app.services.claude_service import ClaudeService
            self.claude = ClaudeService()

        if self.settings.VOYAGE_API_KEY:
            from app.services.embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService()

        has_llm = bool(
            self.settings.ANTHROPIC_API_KEY
            or self.settings.OPENAI_API_KEY
            or self.settings.GEMINI_API_KEY
        )
        if has_llm:
            from app.services.llm_service import LLMService
            self._llm = LLMService(db=db)

    # ================================================================
    # Main entry point
    # ================================================================

    def process_resource(self, resource_id: uuid.UUID) -> dict:
        """Main pipeline: copyright → extract → clean → structure → chunk → embed → store → cleanup."""
        resource = self.db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            return {"error": True, "message": "資源不存在"}

        resource.status = ResourceStatus.PROCESSING
        self.db.commit()

        try:
            # Step 0: Copyright check (PDF only)
            resource_type = resource.type.value if hasattr(resource.type, "value") else str(resource.type)
            if resource_type == "pdf":
                file_path = self._resolve_file_path(resource)
                pdf_bytes = Path(file_path).read_bytes()
                self._check_copyright(pdf_bytes)

            # Step 1: Extract text
            extracted = self._extract_text(resource)
            if not extracted.get("sections"):
                raise ValueError("文件解析未產出任何內容")

            # Step 2: Clean text
            if resource_type == "pdf":
                extracted["sections"] = self._clean_page_texts(extracted["sections"])

            # Step 3: AI structure analysis (regroup flat pages into chapters)
            if resource_type == "pdf" and len(extracted["sections"]) > 3:
                structured = self._analyze_document_structure(extracted["sections"], extracted.get("title", ""))
                if structured:
                    extracted["sections"] = structured

            # Step 4: Delete old data (for reprocessing)
            self.chunk_repo.delete_by_resource_id(resource_id)
            self.db.query(KnowledgeNode).filter_by(resource_id=resource_id).delete()
            self.db.flush()

            # Step 5: Create multi-level knowledge nodes
            nodes = self._create_knowledge_nodes(resource, extracted)

            # Step 6: Smart chunking
            chunks_data = self._chunk_sections(extracted["sections"])

            # Step 7: Embed
            chunk_texts = [c["content"] for c in chunks_data]
            embeddings = [None] * len(chunk_texts)
            if self.embedding_service:
                try:
                    embeddings = self.embedding_service.embed_texts(chunk_texts)
                except Exception as e:
                    logger.warning("Embedding failed: %s", e)

            # Step 8: Store chunks
            self._store_chunks(resource, chunks_data, embeddings, nodes)

            # Step 9: Save normalized markdown
            md_path = self._save_normalized_markdown(resource, extracted)

            # Step 10: Cleanup original file
            self._cleanup_original_file(resource)

            resource.status = ResourceStatus.COMPLETED
            self.db.commit()

            return {
                "status": "completed",
                "chunks_created": len(chunks_data),
                "nodes_created": len(nodes),
                "markdown_path": md_path,
            }

        except Exception as e:
            logger.exception("Document processing failed for resource %s", resource_id)
            self.db.rollback()
            resource = self.db.query(Resource).filter_by(id=resource_id).first()
            if resource:
                resource.status = ResourceStatus.FAILED
                resource.error_message = str(e)[:500]
                self.db.commit()
            return {"error": True, "message": str(e)}

    # ================================================================
    # Step 0: Copyright Check
    # ================================================================

    def _check_copyright(self, pdf_bytes: bytes):
        """Scan first 2 pages for copyright/restricted keywords. Raises if found."""
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            sample_text = ""
            for i in range(min(2, len(doc))):
                sample_text += doc[i].get_text() + "\n"
            doc.close()
        except Exception:
            return  # Can't extract → skip check

        for kw in COPYRIGHT_KEYWORDS:
            if kw.lower() in sample_text.lower():
                raise ValueError(
                    f"偵測到版權限制關鍵字「{kw}」，請確認您擁有此文件的合法使用授權後重新上傳。"
                )

    # ================================================================
    # Step 1: Text Extraction
    # ================================================================

    def _extract_text(self, resource: Resource) -> dict:
        """Extract structured text from resource by type."""
        resource_type = resource.type.value if hasattr(resource.type, "value") else str(resource.type)
        if resource_type == "pdf":
            return self._extract_from_pdf(resource)
        elif resource_type in ("markdown", "txt"):
            return self._extract_from_text_file(resource)
        elif resource_type == "image":
            return self._extract_from_image(resource)
        else:
            raise ValueError(f"不支援的資源類型: {resource_type}")

    def _extract_from_pdf(self, resource: Resource) -> dict:
        """Extract text from PDF using pymupdf, fallback to Claude for scanned PDFs."""
        file_path = self._resolve_file_path(resource)
        pdf_bytes = Path(file_path).read_bytes()

        # Try local extraction first
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages = []
            for i in range(len(doc)):
                text = doc[i].get_text()
                if text.strip():
                    pages.append({"page_num": i + 1, "content": text.strip()})
            doc.close()
            if pages:
                sections = [
                    {"title": f"p.{p['page_num']}", "content": p["content"],
                     "page_start": p["page_num"], "page_end": p["page_num"], "depth": 1}
                    for p in pages
                ]
                return {"title": resource.name, "sections": sections}
        except Exception as e:
            logger.warning("Local PDF extraction failed: %s", e)

        # Fallback: Claude Vision for scanned PDFs
        if self.claude:
            try:
                from app.services.document_processing_service import PDF_EXTRACTION_PROMPT
                raw = self.claude.parse_pdf(pdf_bytes, "請分析此 PDF 並以 JSON 回傳結構化內容。")
                return self._parse_json_response(raw)
            except Exception as e:
                logger.warning("Claude PDF parsing failed: %s", e)

        raise ValueError("無法解析 PDF 文件")

    def _extract_from_text_file(self, resource: Resource) -> dict:
        """Read text/markdown file and split by headers."""
        file_path = self._resolve_file_path(resource)
        content = Path(file_path).read_text(encoding="utf-8")

        sections = []
        current_title = resource.name
        current_depth = 1
        current_content: list[str] = []

        for line in content.split("\n"):
            if line.startswith("### "):
                if current_content:
                    sections.append({"title": current_title, "content": "\n".join(current_content).strip(),
                                     "page_start": None, "page_end": None, "depth": current_depth})
                current_title = line.lstrip("# ").strip()
                current_depth = 3
                current_content = []
            elif line.startswith("## "):
                if current_content:
                    sections.append({"title": current_title, "content": "\n".join(current_content).strip(),
                                     "page_start": None, "page_end": None, "depth": current_depth})
                current_title = line.lstrip("# ").strip()
                current_depth = 2
                current_content = []
            elif line.startswith("# "):
                if current_content:
                    sections.append({"title": current_title, "content": "\n".join(current_content).strip(),
                                     "page_start": None, "page_end": None, "depth": current_depth})
                current_title = line.lstrip("# ").strip()
                current_depth = 1
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append({"title": current_title, "content": "\n".join(current_content).strip(),
                             "page_start": None, "page_end": None, "depth": current_depth})

        return {"title": resource.name, "sections": sections}

    def _extract_from_image(self, resource: Resource) -> dict:
        """Extract text from image using Claude Vision OCR."""
        if not self.claude:
            raise ValueError("圖片 OCR 需要設定 ANTHROPIC_API_KEY")
        file_path = self._resolve_file_path(resource)
        image_bytes = Path(file_path).read_bytes()
        ext = Path(file_path).suffix.lower()
        media_type = IMAGE_MEDIA_TYPES.get(ext, "image/png")
        text = self.claude.parse_image(image_bytes, media_type, IMAGE_OCR_PROMPT)
        return {"title": resource.name, "sections": [
            {"title": resource.name, "content": text, "page_start": None, "page_end": None, "depth": 1}
        ]}

    # ================================================================
    # Step 2: Text Cleaning
    # ================================================================

    def _clean_page_texts(self, sections: list[dict]) -> list[dict]:
        """Remove repetitive headers/footers, watermarks, and page numbers."""
        if len(sections) < 3:
            return sections

        # Detect repetitive lines (appearing in 50%+ of pages)
        line_counter: Counter = Counter()
        for s in sections:
            lines = set()
            for line in s["content"].split("\n"):
                stripped = line.strip()
                if stripped and len(stripped) < 80:  # Only check short lines
                    lines.add(stripped)
            for line in lines:
                line_counter[line] += 1

        threshold = len(sections) * 0.5
        repetitive_lines = {line for line, count in line_counter.items() if count >= threshold}

        # Clean each section
        cleaned = []
        for s in sections:
            lines = s["content"].split("\n")
            filtered = []
            for line in lines:
                stripped = line.strip()
                # Skip repetitive headers/footers
                if stripped in repetitive_lines:
                    continue
                # Skip pure page number lines
                if re.match(r'^[\d\-\.]+$', stripped):
                    continue
                # Skip special characters (PDF artifacts)
                if stripped and all(ord(c) > 0xF000 for c in stripped):
                    continue
                filtered.append(line)

            content = "\n".join(filtered).strip()
            if content:
                cleaned.append({**s, "content": content})

        return cleaned if cleaned else sections

    # ================================================================
    # Step 3: AI Document Structure Analysis
    # ================================================================

    def _analyze_document_structure(self, sections: list[dict], doc_title: str) -> list[dict] | None:
        """Use AI to analyze document structure and produce multi-level chapters.

        Returns restructured sections with depth 1-3, or None if AI unavailable/fails.
        """
        if not self._llm:
            return None

        # Build page summaries for AI
        summaries = []
        for s in sections[:40]:
            preview = s["content"][:120].replace('\n', ' ').strip()
            page = s.get("page_start", "?")
            summaries.append(f"p.{page}: {preview}")

        try:
            result = self._llm.generate(
                STRUCTURE_ANALYSIS_PROMPT,
                f"文件：{doc_title}\n\n" + "\n".join(summaries),
                max_tokens=8000,
            )

            parsed = self._parse_json_response(result)
            chapters = parsed.get("chapters", [])
            if not chapters:
                logger.warning("AI structure analysis returned no chapters")
                return None

            logger.info("AI structure analysis: %d chapters", len(chapters))
            return self._flatten_structure(chapters, sections)

        except Exception as e:
            logger.warning("AI structure analysis failed: %s", e)
            return None

    def _flatten_structure(self, chapters: list[dict], original_sections: list[dict]) -> list[dict]:
        """Convert nested chapter structure to flat section list with depth."""
        # Build page → content map from original sections
        page_content: dict[int, str] = {}
        max_page = 0
        for s in original_sections:
            pn = s.get("page_start")
            if pn:
                page_content[pn] = s["content"]
                max_page = max(max_page, pn)

        # Infer page_end for chapters that don't have it
        for i, ch in enumerate(chapters):
            if not ch.get("page_end"):
                if i + 1 < len(chapters):
                    ch["page_end"] = chapters[i + 1].get("page_start", ch.get("page_start", 0)) - 1
                else:
                    ch["page_end"] = max_page
            # Same for sections
            for j, sec in enumerate(ch.get("sections", [])):
                if not sec.get("page_end"):
                    if j + 1 < len(ch.get("sections", [])):
                        sec["page_end"] = ch["sections"][j + 1].get("page_start", sec.get("page_start", 0)) - 1
                    else:
                        sec["page_end"] = ch["page_end"]

        result = []
        for ch in chapters:
            page_start = ch.get("page_start", 0)
            page_end = ch.get("page_end", page_start)

            # Chapter content: merge pages in range
            ch_content = "\n\n".join(
                page_content.get(p, "") for p in range(page_start, page_end + 1) if page_content.get(p)
            )

            ch_sections = ch.get("sections", [])
            if ch_sections:
                # Has sub-sections: chapter is a container, add sub-sections with content
                for sec in ch_sections:
                    sec_start = sec.get("page_start", page_start)
                    sec_end = sec.get("page_end", sec_start)
                    sec_content = "\n\n".join(
                        page_content.get(p, "") for p in range(sec_start, sec_end + 1) if page_content.get(p)
                    )

                    subsections = sec.get("subsections", [])
                    if subsections:
                        for sub in subsections:
                            sub_page = sub.get("page_start", sec_start)
                            sub_content = page_content.get(sub_page, "")
                            result.append({
                                "title": sub.get("title", f"p.{sub_page}"),
                                "content": sub_content,
                                "page_start": sub_page, "page_end": sub_page,
                                "depth": 3, "parent_title": sec.get("title", ""),
                            })
                    else:
                        result.append({
                            "title": sec.get("title", f"p.{sec_start}"),
                            "content": sec_content,
                            "page_start": sec_start, "page_end": sec_end,
                            "depth": 2, "parent_title": ch.get("title", ""),
                        })
            else:
                # No sub-sections: chapter is a leaf
                result.append({
                    "title": ch.get("title", f"p.{page_start}"),
                    "content": ch_content,
                    "page_start": page_start, "page_end": page_end,
                    "depth": 1,
                })

        return result if result else None

    # ================================================================
    # Step 4: Smart Chunking
    # ================================================================

    def _chunk_sections(self, sections: list[dict]) -> list[dict]:
        """Smart chunking: respect section boundaries, then paragraph-based, then token sliding window."""
        chunk_size = self.settings.CHUNK_SIZE_TOKENS
        overlap = self.settings.CHUNK_OVERLAP_TOKENS
        all_chunks: list[dict] = []
        chunk_index = 0

        for section in sections:
            content = section.get("content", "")
            if not content.strip():
                continue

            tokens = self.tokenizer.encode(content)
            section_title = section.get("title", "")
            page_start = section.get("page_start")
            page_end = section.get("page_end")
            depth = section.get("depth", 1)

            if len(tokens) <= chunk_size:
                # Section fits in a single chunk — keep it whole
                all_chunks.append({
                    "content": content, "token_count": len(tokens),
                    "source_page_start": page_start, "source_page_end": page_end,
                    "section_title": section_title, "depth": depth, "chunk_index": chunk_index,
                })
                chunk_index += 1
            else:
                # Try paragraph-based splitting first
                paragraphs = re.split(r'\n\n+', content)
                current_chunk = ""
                current_tokens = 0

                for para in paragraphs:
                    para_tokens = len(self.tokenizer.encode(para))

                    if current_tokens + para_tokens <= chunk_size:
                        current_chunk += ("\n\n" if current_chunk else "") + para
                        current_tokens += para_tokens
                    else:
                        # Save current chunk
                        if current_chunk:
                            all_chunks.append({
                                "content": current_chunk, "token_count": current_tokens,
                                "source_page_start": page_start, "source_page_end": page_end,
                                "section_title": section_title, "depth": depth, "chunk_index": chunk_index,
                            })
                            chunk_index += 1

                        # If single paragraph exceeds chunk_size, use token sliding window
                        if para_tokens > chunk_size:
                            para_toks = self.tokenizer.encode(para)
                            start = 0
                            while start < len(para_toks):
                                end = min(start + chunk_size, len(para_toks))
                                chunk_text = self.tokenizer.decode(para_toks[start:end])
                                all_chunks.append({
                                    "content": chunk_text, "token_count": end - start,
                                    "source_page_start": page_start, "source_page_end": page_end,
                                    "section_title": section_title, "depth": depth, "chunk_index": chunk_index,
                                })
                                chunk_index += 1
                                if end >= len(para_toks):
                                    break
                                start = end - overlap
                            current_chunk = ""
                            current_tokens = 0
                        else:
                            current_chunk = para
                            current_tokens = para_tokens

                # Don't forget the last chunk
                if current_chunk:
                    all_chunks.append({
                        "content": current_chunk, "token_count": current_tokens,
                        "source_page_start": page_start, "source_page_end": page_end,
                        "section_title": section_title, "depth": depth, "chunk_index": chunk_index,
                    })
                    chunk_index += 1

        return all_chunks

    # ================================================================
    # Step 5: Multi-level Knowledge Nodes
    # ================================================================

    def _create_knowledge_nodes(self, resource: Resource, extracted: dict) -> list[KnowledgeNode]:
        """Create multi-level knowledge node tree (depth 0-3)."""
        nodes: list[KnowledgeNode] = []

        # Root node (depth 0)
        root = KnowledgeNode(
            resource_id=resource.id, parent_id=None,
            name=extracted.get("title", resource.name),
            depth=0, sort_order=0,
        )
        self.db.add(root)
        self.db.flush()
        nodes.append(root)

        # Track parents at each depth level for tree building
        parent_stack = {0: root}  # depth → node

        for i, section in enumerate(extracted.get("sections", [])):
            depth = section.get("depth", 1)
            parent_depth = depth - 1
            parent = parent_stack.get(parent_depth, root)

            node = KnowledgeNode(
                resource_id=resource.id,
                parent_id=parent.id,
                name=section.get("title", f"段落 {i + 1}"),
                depth=depth,
                sort_order=i + 1,
                source_page_number=section.get("page_start"),
                source_text=section.get("content", "")[:500],
            )
            self.db.add(node)
            self.db.flush()
            nodes.append(node)
            parent_stack[depth] = node

        return nodes

    # ================================================================
    # Step 6: Store Chunks
    # ================================================================

    def _store_chunks(self, resource, chunks_data, embeddings, nodes):
        """Store ResourceChunk instances with embeddings."""
        # Build (title, depth) → node_id mapping
        node_map: dict[tuple[str, int], uuid.UUID] = {}
        for node in nodes[1:]:
            node_map[(node.name, node.depth)] = node.id

        chunks = []
        for i, cd in enumerate(chunks_data):
            key = (cd.get("section_title", ""), cd.get("depth", 1))
            node_id = node_map.get(key)
            # Fallback: try matching by title only
            if not node_id:
                for (t, d), nid in node_map.items():
                    if t == cd.get("section_title", ""):
                        node_id = nid
                        break

            chunk = ResourceChunk(
                resource_id=resource.id, node_id=node_id,
                chunk_index=cd["chunk_index"], content=cd["content"],
                token_count=cd["token_count"],
                source_page_start=cd.get("source_page_start"),
                source_page_end=cd.get("source_page_end"),
                metadata_json={"section_title": cd.get("section_title", ""), "depth": cd.get("depth", 1)},
                embedding=embeddings[i] if i < len(embeddings) else None,
            )
            chunks.append(chunk)

        self.chunk_repo.save_batch(chunks)

    # ================================================================
    # Step 7: Markdown Normalization
    # ================================================================

    def _save_normalized_markdown(self, resource: Resource, extracted: dict) -> str | None:
        """Save a normalized .md version of the document."""
        sections = extracted.get("sections", [])
        if not sections:
            return None

        lines = [f"# {extracted.get('title', resource.name)}\n"]

        for s in sections:
            depth = s.get("depth", 1)
            heading = "#" * (depth + 1)  # depth 1 → ##, depth 2 → ###
            title = s.get("title", "")
            content = s.get("content", "")
            page = s.get("page_start")

            if title:
                page_ref = f" (p.{page})" if page else ""
                lines.append(f"\n{heading} {title}{page_ref}\n")
            if content:
                lines.append(f"{content}\n")

        md_content = "\n".join(lines)

        # Save to uploads directory
        user_id = str(resource.user_id)
        upload_dir = Path(__file__).parent.parent.parent / "uploads" / user_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        md_path = upload_dir / f"{resource.id}.md"
        md_path.write_text(md_content, encoding="utf-8")

        logger.info("Saved normalized markdown: %s (%d chars)", md_path, len(md_content))
        return str(md_path)

    # ================================================================
    # Step 8: Original File Cleanup
    # ================================================================

    def _cleanup_original_file(self, resource: Resource):
        """Delete original PDF/image after successful processing. Keep .md.

        使用 StorageService 統一刪除（本地/GCS 都支援）。
        注意：不再清空 gcs_path，保留以供後續溯源。
        """
        if not resource.gcs_path:
            return

        # 不刪除 markdown 檔案
        if resource.gcs_path.lower().endswith(".md"):
            return

        try:
            self.storage.delete_file(resource.gcs_path)
            logger.info("Deleted original file via storage service: %s", resource.gcs_path)
            # 保留 gcs_path 記錄但標記為已清理
            # resource.gcs_path 不再設為 None
        except Exception as e:
                logger.warning("Failed to delete original file: %s", e)

    # ================================================================
    # Utilities
    # ================================================================

    def _resolve_file_path(self, resource: Resource) -> str:
        """取得可讀取的本地檔案路徑。

        - 本地模式：gcs_path 就是本地路徑，直接回傳
        - GCS 模式：下載到 /tmp 暫存目錄
        """
        if not resource.gcs_path:
            raise ValueError("資源無檔案路徑（gcs_path 未設定，請確認上傳流程是否正確）")

        # GCS 路徑：下載到暫存目錄
        if resource.gcs_path.startswith("gs://"):
            return self.storage.download_to_temp(resource.gcs_path)

        # 本地路徑：直接回傳（但檢查是否存在）
        if Path(resource.gcs_path).exists():
            return resource.gcs_path

        raise ValueError(f"檔案不存在: {resource.gcs_path}")

    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from LLM response, handling markdown blocks and truncation."""
        text = text.strip()
        if "```" in text:
            lines = text.split("\n")
            inner = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    inner.append(line)
            text = "\n".join(inner)

        text = text.strip()

        # Replace curly/CJK quotes
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u300c', '"').replace('\u300d', '"')

        # Try parsing as-is first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fix truncated JSON: find last complete object and close brackets
        # Strategy: remove incomplete trailing entry, then close all open brackets
        last_complete = max(text.rfind("},"), text.rfind("}]"))
        if last_complete > 0:
            text = text[:last_complete + 1]
            # Count unclosed brackets
            opens = text.count("[") - text.count("]")
            braces = text.count("{") - text.count("}")
            text += "]" * opens + "}" * braces

        return json.loads(text)
