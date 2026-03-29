"""DocumentProcessingService — orchestrates PDF→Claude→chunks→embeddings pipeline.

Supports two modes:
  - Full AI mode: Claude parses PDF/images, Voyage AI generates embeddings (requires API keys)
  - Local mode: extracts text locally for TXT/Markdown/PDF, skips embeddings (no API keys needed)
"""

import json
import logging
import re
import uuid
from pathlib import Path

import tiktoken
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceStatus
from app.models.resource_chunk import ResourceChunk
from app.repositories.resource_chunk_repository import ResourceChunkRepository

logger = logging.getLogger(__name__)

# Media type mapping for image files
IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}

PDF_EXTRACTION_PROMPT = """請分析這份 PDF 文件，並以 JSON 格式回傳其結構化內容。

要求：
1. 將文件拆分為有意義的章節（sections）
2. 每個 section 包含：title（標題）、content（該段落的完整內容）、page_start（起始頁碼）、page_end（結束頁碼）
3. 保留原文內容，不要摘要或省略
4. 如果有表格，將其轉為 Markdown 表格格式
5. 數學公式保留原始表達

回傳格式：
```json
{
  "title": "文件標題",
  "sections": [
    {
      "title": "章節標題",
      "content": "章節完整內容...",
      "page_start": 1,
      "page_end": 2
    }
  ]
}
```"""

IMAGE_OCR_PROMPT = """請辨識這張圖片中的所有文字內容，並以結構化方式輸出。

要求：
1. 完整辨識所有可見文字
2. 保留段落結構
3. 如有表格，轉為 Markdown 表格格式
4. 如有數學公式，保留原始表達

以純文字格式回傳辨識結果。"""


class DocumentProcessingService:
    """Orchestrates the full document processing pipeline:
    upload → parse → chunk → embed → store.
    """

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.chunk_repo = ResourceChunkRepository(db)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # AI services — only initialized when API keys are available
        self.claude = None
        self.embedding_service = None

        if self.settings.ANTHROPIC_API_KEY:
            from app.services.claude_service import ClaudeService
            self.claude = ClaudeService()

        if self.settings.VOYAGE_API_KEY:
            from app.services.embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService()

    def process_resource(self, resource_id: uuid.UUID) -> dict:
        """Main entry point: process a resource end-to-end.

        1. Mark as PROCESSING
        2. Extract text (by type)
        3. Create knowledge nodes
        4. Chunk text
        5. Embed chunks
        6. Store chunks with embeddings
        7. Mark as COMPLETED (or FAILED)
        """
        resource = self.db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            return {"error": True, "message": "資源不存在"}

        # Mark as processing
        resource.status = ResourceStatus.PROCESSING
        self.db.commit()

        try:
            # Step 1: Extract text
            extracted = self._extract_text(resource)
            if not extracted.get("sections"):
                raise ValueError("文件解析未產出任何內容")

            # Step 2: Delete old chunks (for reprocessing)
            self.chunk_repo.delete_by_resource_id(resource_id)
            # Delete old knowledge nodes
            self.db.query(KnowledgeNode).filter_by(resource_id=resource_id).delete()
            self.db.flush()

            # Step 3: Create knowledge nodes
            nodes = self._create_knowledge_nodes(resource, extracted)

            # Step 4: Chunk text
            chunks_data = self._chunk_sections(extracted["sections"])

            # Step 5: Embed chunks (skip if no Voyage API key or on error)
            chunk_texts = [c["content"] for c in chunks_data]
            embeddings = [None] * len(chunk_texts)
            if self.embedding_service:
                try:
                    embeddings = self.embedding_service.embed_texts(chunk_texts)
                except Exception as e:
                    logger.warning("Embedding failed (chunks saved without vectors): %s", e)
            else:
                logger.info("Skipping embeddings (VOYAGE_API_KEY not set)")

            # Step 6: Store chunks
            self._store_chunks(resource, chunks_data, embeddings, nodes)

            # Step 7: Mark completed
            resource.status = ResourceStatus.COMPLETED
            self.db.commit()

            return {
                "status": "completed",
                "chunks_created": len(chunks_data),
                "nodes_created": len(nodes),
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
        """Extract text from PDF.

        Uses local extraction first (fast, no API cost).
        Falls back to Claude API only when local extraction fails.
        """
        file_path = self._resolve_file_path(resource)
        pdf_bytes = Path(file_path).read_bytes()

        # Try local extraction first (fast, free)
        try:
            result = self._extract_pdf_local(pdf_bytes, resource.name)
            if result.get("sections"):
                return result
        except Exception as e:
            logger.warning("Local PDF extraction failed: %s", e)

        # Fallback to Claude API (for scanned/image-heavy PDFs)
        if self.claude:
            try:
                raw = self.claude.parse_pdf(pdf_bytes, PDF_EXTRACTION_PROMPT)
                try:
                    result = json.loads(raw)
                except json.JSONDecodeError:
                    text = raw.strip()
                    if "```" in text:
                        lines = text.split("\n")
                        json_lines = []
                        in_block = False
                        for line in lines:
                            if line.strip().startswith("```"):
                                in_block = not in_block
                                continue
                            if in_block:
                                json_lines.append(line)
                        result = json.loads("\n".join(json_lines))
                    else:
                        raise
                return result
            except Exception as e:
                logger.warning("Claude PDF parsing also failed: %s", e)

        raise ValueError("無法解析 PDF 文件")

    def _extract_pdf_local(self, pdf_bytes: bytes, name: str) -> dict:
        """Extract text from PDF using local libraries (no API needed).

        Tries pymupdf (fitz) first, then falls back to reading raw bytes.
        """
        # Try pymupdf
        try:
            import fitz  # pymupdf
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            sections = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    sections.append({
                        "title": f"第 {page_num + 1} 頁",
                        "content": text.strip(),
                        "page_start": page_num + 1,
                        "page_end": page_num + 1,
                    })
            doc.close()
            if sections:
                return {"title": name, "sections": sections}
        except ImportError:
            logger.info("pymupdf not installed, trying pdfplumber")
        except Exception as e:
            logger.warning("pymupdf extraction failed: %s", e)

        # Try pdfplumber
        try:
            import pdfplumber
            import io
            sections = []
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        sections.append({
                            "title": f"第 {i + 1} 頁",
                            "content": text.strip(),
                            "page_start": i + 1,
                            "page_end": i + 1,
                        })
            if sections:
                return {"title": name, "sections": sections}
        except ImportError:
            logger.info("pdfplumber not installed")
        except Exception as e:
            logger.warning("pdfplumber extraction failed: %s", e)

        # Final fallback: treat as binary, extract any readable text
        try:
            raw_text = pdf_bytes.decode("utf-8", errors="ignore")
            # Extract text between BT and ET markers (PDF text objects)
            text_parts = re.findall(r'\(([^)]+)\)', raw_text)
            content = " ".join(t for t in text_parts if len(t) > 2)
            if content.strip():
                return {
                    "title": name,
                    "sections": [{"title": name, "content": content[:10000], "page_start": None, "page_end": None}],
                }
        except Exception:
            pass

        raise ValueError("無法解析 PDF 文件（請安裝 pymupdf: pip install pymupdf）")

    def _extract_from_text_file(self, resource: Resource) -> dict:
        """Read text/markdown file and split by headers."""
        file_path = self._resolve_file_path(resource)
        content = Path(file_path).read_text(encoding="utf-8")

        # Split by markdown headers
        sections = []
        current_title = resource.name
        current_content: list[str] = []

        for line in content.split("\n"):
            if line.startswith("# "):
                if current_content:
                    sections.append({
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                        "page_start": None,
                        "page_end": None,
                    })
                current_title = line.lstrip("# ").strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append({
                "title": current_title,
                "content": "\n".join(current_content).strip(),
                "page_start": None,
                "page_end": None,
            })

        return {"title": resource.name, "sections": sections}

    def _extract_from_image(self, resource: Resource) -> dict:
        """Extract text from image using Claude Vision OCR.

        Requires ANTHROPIC_API_KEY — no local fallback for image OCR.
        """
        if not self.claude:
            raise ValueError("圖片 OCR 需要設定 ANTHROPIC_API_KEY")

        file_path = self._resolve_file_path(resource)
        image_bytes = Path(file_path).read_bytes()

        ext = Path(file_path).suffix.lower()
        media_type = IMAGE_MEDIA_TYPES.get(ext, "image/png")

        text = self.claude.parse_image(image_bytes, media_type, IMAGE_OCR_PROMPT)

        return {
            "title": resource.name,
            "sections": [
                {
                    "title": resource.name,
                    "content": text,
                    "page_start": None,
                    "page_end": None,
                }
            ],
        }

    def _resolve_file_path(self, resource: Resource) -> str:
        """Resolve the file path for a resource.

        For now, uses gcs_path as a local file path.
        In production, this would download from GCS first.
        """
        if resource.gcs_path:
            return resource.gcs_path
        raise ValueError("資源無檔案路徑")

    def _create_knowledge_nodes(
        self, resource: Resource, extracted: dict
    ) -> list[KnowledgeNode]:
        """Create hierarchical knowledge nodes from extracted structure."""
        nodes: list[KnowledgeNode] = []

        # Root node
        root = KnowledgeNode(
            resource_id=resource.id,
            parent_id=None,
            name=extracted.get("title", resource.name),
            depth=0,
            sort_order=0,
        )
        self.db.add(root)
        self.db.flush()
        nodes.append(root)

        # Child nodes for each section
        for i, section in enumerate(extracted.get("sections", [])):
            child = KnowledgeNode(
                resource_id=resource.id,
                parent_id=root.id,
                name=section.get("title", f"段落 {i + 1}"),
                depth=1,
                sort_order=i + 1,
                source_page_number=section.get("page_start"),
                source_text=section.get("content", "")[:500],
            )
            self.db.add(child)
            nodes.append(child)

        self.db.flush()
        return nodes

    def _chunk_sections(self, sections: list[dict]) -> list[dict]:
        """Split sections into overlapping chunks using tiktoken."""
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

            if len(tokens) <= chunk_size:
                # Section fits in a single chunk
                all_chunks.append({
                    "content": content,
                    "token_count": len(tokens),
                    "source_page_start": page_start,
                    "source_page_end": page_end,
                    "section_title": section_title,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1
            else:
                # Split into overlapping chunks
                start = 0
                while start < len(tokens):
                    end = min(start + chunk_size, len(tokens))
                    chunk_tokens = tokens[start:end]
                    chunk_text = self.tokenizer.decode(chunk_tokens)

                    all_chunks.append({
                        "content": chunk_text,
                        "token_count": len(chunk_tokens),
                        "source_page_start": page_start,
                        "source_page_end": page_end,
                        "section_title": section_title,
                        "chunk_index": chunk_index,
                    })
                    chunk_index += 1

                    if end >= len(tokens):
                        break
                    start = end - overlap

        return all_chunks

    def _store_chunks(
        self,
        resource: Resource,
        chunks_data: list[dict],
        embeddings: list[list[float]],
        nodes: list[KnowledgeNode],
    ) -> None:
        """Create and store ResourceChunk instances with embeddings."""
        # Build section_title → node_id mapping (child nodes start at index 1)
        section_node_map: dict[str, uuid.UUID] = {}
        for node in nodes[1:]:  # skip root
            section_node_map[node.name] = node.id

        chunks = []
        for i, chunk_data in enumerate(chunks_data):
            # Find the matching knowledge node by section title
            node_id = section_node_map.get(chunk_data.get("section_title", ""))

            chunk = ResourceChunk(
                resource_id=resource.id,
                node_id=node_id,
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                token_count=chunk_data["token_count"],
                source_page_start=chunk_data.get("source_page_start"),
                source_page_end=chunk_data.get("source_page_end"),
                metadata_json={"section_title": chunk_data.get("section_title", "")},
                embedding=embeddings[i] if i < len(embeddings) else None,
            )
            chunks.append(chunk)

        self.chunk_repo.save_batch(chunks)
