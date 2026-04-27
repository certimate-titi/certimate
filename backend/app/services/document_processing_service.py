"""DocumentProcessingService — orchestrates the full document processing pipeline.

Two-layer architecture:
  Layer 1: Media Extraction (pure engineering, no LLM)
    - PDF/DOCX/PPTX/XLSX/DOC/PPT/XLS → text extraction
    - Image → OCR (Claude Vision)
    - Audio/Video → Whisper API transcription
    - YouTube → yt-dlp subtitles / Whisper fallback
  Layer 2: K-01 Unified Prompt (Gemini Flash)
    - Raw text → structured Markdown

Pipeline:
  0. Copyright check (PDF only)
  1. Layer 1: Media extraction (via media_extractors module)
  2. Layer 2: K-01 LLM structuring (optional, for non-text formats)
  3. Text cleaning (remove headers/footers/watermarks)
  4. AI structure analysis (chapters → sections → subsections)
  5. Smart chunking (by section boundaries, then token-based)
  6. Multi-level knowledge node creation
  7. Embedding (Voyage AI → pgvector)
  8. Markdown normalization & storage
  9. Original file cleanup
  10. Unified knowledge tree extraction trigger
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

# Fallback prompts（DB 模板不可用時使用）
_FALLBACK_IMAGE_OCR = """請辨識這張圖片中的所有文字內容，並以結構化方式輸出。
要求：1. 完整辨識所有可見文字 2. 保留段落結構 3. 表格轉 Markdown 4. 數學公式保留原始表達
以純文字格式回傳辨識結果。"""

_FALLBACK_STRUCTURE_ANALYSIS = (
    "分析文件結構，產出章節目錄 JSON。1-3 層深度（章→節→小節）。\n"
    "標題要簡短（15字內）。只回傳 JSON，不要 markdown。\n"
    '格式：{"chapters":[{"title":"章","page_start":1,"page_end":5,'
    '"sections":[{"title":"節","page_start":1,"page_end":2}]}]}'
)

# Legacy aliases for backward compatibility
IMAGE_OCR_PROMPT = _FALLBACK_IMAGE_OCR
STRUCTURE_ANALYSIS_PROMPT = _FALLBACK_STRUCTURE_ANALYSIS


def _classify_processing_error(e: Exception) -> str:
    """Turn a raw exception into a user-friendly, categorized reason.

    UI shows this verbatim via Resource.error_message, so it must read naturally
    and tell the user which stage failed and why.
    """
    msg = str(e)
    if "偵測到版權" in msg or "COPYRIGHT" in msg.upper():
        return f"【版權限制】{msg}"
    if "Voyage" in msg and ("預算" in msg or "quota" in msg.lower()):
        return f"【系統配額】{msg}"
    if "媒體萃取失敗" in msg or "無法從" in msg:
        return f"【萃取失敗】{msg}"
    if "檔案無法轉換為 Markdown" in msg or "未產出任何" in msg:
        return f"【轉檔失敗】{msg}"
    if "embedding" in msg.lower() or "vector" in msg.lower():
        return f"【向量化失敗】{msg}"
    if "timeout" in msg.lower() or "timed out" in msg.lower():
        return f"【處理逾時】{msg}（檔案可能過大，請分批上傳或稍後重試）"
    return f"【處理失敗】{msg}"


class DocumentProcessingService:
    """Full document processing pipeline: upload → parse → chunk → embed → store."""

    def __init__(self, db: Session):
        """初始化實例。"""
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

        # Prompt template service for DB-managed prompts
        self._prompt_svc = None
        try:
            from app.services.prompt_template_service import PromptTemplateService
            self._prompt_svc = PromptTemplateService(db)
        except Exception:
            pass

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """Load prompt template from DB. Returns dict or None (caller uses fallback)."""
        if not self._prompt_svc:
            return None
        try:
            result = self._prompt_svc.get_prompt_for_ai(name)
            if result.get("error"):
                return None
            if variables:
                render = self._prompt_svc.render_prompt
                result["system_prompt"] = render(result["system_prompt"], variables)
                result["user_prompt"] = render(result["user_prompt"], variables)
            return result
        except Exception:
            return None

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

            # Step 1 + 1.5: Layer 1 media extraction → Layer 2 K-01 structuring
            try:
                extracted = self._extract_text(resource)
            except Exception as e:
                raise ValueError(
                    f"媒體萃取失敗（無法從 {resource_type.upper()} 讀取文字內容）：{str(e)[:200]}"
                ) from e
            if not extracted.get("sections"):
                raise ValueError(
                    f"檔案無法轉換為 Markdown：{resource_type.upper()} 未產出任何可用文字。"
                    "可能原因：純圖片 / 掃描檔（需先 OCR）、內容過短、或檔案格式異常。"
                )

            # Step 1.7: PDF 4-tier structure analysis (replaces raw page splits)
            if resource_type == "pdf":
                pdf_path = file_path  # set in Step 0 copyright check above
                pdf_structured = self._analyze_pdf_structure(
                    pdf_path, extracted["sections"], extracted.get("title", "")
                )
                if pdf_structured:
                    extracted["sections"] = pdf_structured

            # Step 2: Clean text (PDF/DOCX page-based formats)
            if resource_type in ("pdf", "docx", "doc"):
                extracted["sections"] = self._clean_page_texts(extracted["sections"])

            # Step 3: AI structure analysis (regroup flat pages into chapters)
            if resource_type in ("pdf", "docx", "doc") and len(extracted["sections"]) > 3:
                structured = self._analyze_document_structure(extracted["sections"], extracted.get("title", ""))
                if structured:
                    extracted["sections"] = structured

            # Step 4: Delete old data (for reprocessing) — use hard delete to
            # avoid chunk_index unique conflicts with soft-deleted rows
            self.chunk_repo.delete_by_resource_id(resource_id, hard=True)
            self.db.query(KnowledgeNode).filter_by(resource_id=resource_id).delete()
            self.db.flush()

            # Step 5: Create multi-level knowledge nodes
            nodes = self._create_knowledge_nodes(resource, extracted)

            # Step 6: Smart chunking
            chunks_data = self._chunk_sections(extracted["sections"])

            # Step 7: Embed (with Voyage quota gate — Feature 33)
            chunk_texts = [c["content"] for c in chunks_data]
            embeddings = [None] * len(chunk_texts)

            # Voyage 配額鎖：在實際呼叫 Voyage API 前檢查當月預算
            from app.services.voyage_quota_service import (
                VoyageQuotaDegraded,
                VoyageQuotaExceeded,
                VoyageQuotaService,
            )
            from app.middleware.ai_usage_tracker import (
                estimate_voyage_cost,
                track_ai_usage,
            )
            from decimal import Decimal

            est_tokens = sum(len(t) for t in chunk_texts) // 4 or 1
            est_cost = estimate_voyage_cost(est_tokens)
            quota_svc = VoyageQuotaService(self.db)

            try:
                quota_svc.check_and_reserve(est_cost)
            except VoyageQuotaDegraded:
                # 達 80% 降級門檻：標記資源為 PENDING_BUDGET_RECOVERY 並中止本次處理
                resource.status = ResourceStatus.PENDING_BUDGET_RECOVERY
                self.db.commit()
                logger.warning(
                    "Resource %s queued for budget recovery (Voyage degraded)",
                    resource_id,
                )
                return {
                    "ok": True,
                    "status": "PENDING_BUDGET_RECOVERY",
                    "resource_id": resource_id,
                    "message": "AI 資源處理已排隊，因本月 embedding 預算已達降級門檻",
                }
            except VoyageQuotaExceeded:
                resource.status = ResourceStatus.FAILED
                resource.error_message = "Voyage 月度預算已耗盡（100%），請聯繫管理員擴充預算"
                self.db.commit()
                logger.error(
                    "Resource %s failed: Voyage quota exhausted",
                    resource_id,
                )
                raise

            if self.embedding_service:
                try:
                    with track_ai_usage(
                        self.db, provider="voyage", feature="document_embedding"
                    ) as tracker:
                        embeddings = self.embedding_service.embed_texts(chunk_texts)
                        tracker.input_tokens = est_tokens
                        tracker.cost_usd = est_cost
                        tracker.endpoint = "voyage/embed"
                except Exception as e:
                    logger.warning("Embedding failed: %s", e)

            # Step 8: Store chunks
            self._store_chunks(resource, chunks_data, embeddings, nodes)

            # Step 9: Save normalized markdown
            md_path = self._save_normalized_markdown(resource, extracted)

            # Step 10: 注意 — 不在此處 cleanup 原始檔，
            # parse_job (Gemini 多模態) 還需要原始 PDF。
            # cleanup 移到 _process_resource_background 在 parse_job 成功後執行。

            resource.status = ResourceStatus.COMPLETED
            self.db.commit()

            # Step 11: 自動觸發統一知識樹萃取（如果資源有 subject_id）
            extraction_result = None
            if resource.subject_id:
                try:
                    from app.services.unified_knowledge_extraction_service import (
                        UnifiedKnowledgeExtractionService,
                    )
                    extractor = UnifiedKnowledgeExtractionService(self.db)
                    extraction_result = extractor.extract(str(resource.subject_id))
                    if extraction_result.get("error"):
                        logger.warning(
                            "Unified extraction warning for subject %s: %s",
                            resource.subject_id, extraction_result.get("message")
                        )
                except Exception as e:
                    logger.warning("Unified extraction skipped: %s", e)

            return {
                "status": "completed",
                "chunks_created": len(chunks_data),
                "nodes_created": len(nodes),
                "markdown_path": md_path,
                "extraction": extraction_result,
            }

        except Exception as e:
            logger.exception("Document processing failed for resource %s", resource_id)
            self.db.rollback()
            resource = self.db.query(Resource).filter_by(id=resource_id).first()
            if resource:
                resource.status = ResourceStatus.FAILED
                resource.error_message = _classify_processing_error(e)[:500]
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
    # Step 1: Layer 1 — Media Extraction (pure engineering, no LLM)
    # ================================================================

    def _extract_text(self, resource: Resource) -> dict:
        """Layer 1: Extract raw text using media_extractors module.

        Dispatches to the appropriate extractor based on resource type.
        For non-text formats, follows up with Layer 2 (K-01 LLM structuring).
        """
        from app.services.media_extractors import extract as media_extract
        from app.services.media_extractors.base import ExtractionResult

        resource_type = resource.type.value if hasattr(resource.type, "value") else str(resource.type)

        # Resolve file path (YouTube uses URL directly)
        if resource_type == "youtube":
            file_path = resource.youtube_url or resource.name
        else:
            file_path = self._resolve_file_path(resource)

        # Get OCR prompt for image extraction
        ocr_prompt = None
        if resource_type == "image":
            db_prompt = self._load_prompt("image_ocr_recognition")
            ocr_prompt = db_prompt["system_prompt"] if db_prompt else IMAGE_OCR_PROMPT

        # Layer 1: Media extraction
        result: ExtractionResult = media_extract(
            resource_type,
            file_path,
            resource_name=resource.name,
            claude_service=self.claude,
            ocr_prompt=ocr_prompt,
        )

        # Layer 2: K-01 LLM structuring (for formats that benefit from it)
        # PDF already has page-level sections from pymupdf; skip K-01 to avoid truncation
        needs_llm_structuring = resource_type not in ("markdown", "txt", "pdf")
        if needs_llm_structuring and result.raw_text and self._llm:
            structured = self._apply_k01_structuring(result)
            if structured:
                return structured

        # Use pre-split sections from extractor, or create single section
        if result.sections:
            return {"title": result.title, "sections": result.sections}
        else:
            return {"title": result.title, "sections": [{
                "title": result.title,
                "content": result.raw_text,
                "page_start": None, "page_end": None, "depth": 1,
            }]}

    # ================================================================
    # Step 1.5: Layer 2 — K-01 LLM Structuring
    # ================================================================

    # Fallback K-01 prompt（DB 模板不可用時使用）
    _FALLBACK_K01_SYSTEM = """你是專業的教育文件解析器。將以下原始內容轉換為結構化 Markdown。

規則：
1. 保留原始標題層級（#, ##, ###）
2. 表格轉為 Markdown table
3. 數學公式轉為 KaTeX 格式（$...$）
4. 移除頁首頁尾、浮水印、頁碼
5. 保留項目符號列表結構
6. 程式碼區塊使用 ``` 包裹並標注語言
7. 不添加任何原文中沒有的內容
8. 重要概念以粗體標記
9. 逐字稿內容：每 3-5 分鐘自動分段加小標題、保留時間戳、口語轉書面語
10. 投影片內容：每張投影片作為一個 section
11. 全繁體中文"""

    def _apply_k01_structuring(self, extraction_result) -> dict | None:
        """Layer 2: Use K-01 prompt to convert raw text → structured Markdown.

        Returns structured dict or None if LLM unavailable/fails.
        """
        if not self._llm:
            return None

        raw_text = extraction_result.raw_text
        if not raw_text or len(raw_text.strip()) < 20:
            return None

        # Truncate extremely long content to avoid token limits
        max_chars = 60000  # ~15K tokens
        if len(raw_text) > max_chars:
            raw_text = raw_text[:max_chars] + "\n\n[...內容已截斷...]"

        # Try DB template first
        db_prompt = self._load_prompt("resource_to_markdown", {
            "content_type": extraction_result.content_type,
            "source_name": extraction_result.title,
            "raw_content": raw_text,
            "metadata": extraction_result.metadata,
        })

        if db_prompt:
            system_prompt = db_prompt["system_prompt"]
            user_prompt = db_prompt["user_prompt"]
        else:
            system_prompt = self._FALLBACK_K01_SYSTEM
            user_prompt = (
                f"來源：{extraction_result.title}（{extraction_result.content_type}）\n"
                f"{extraction_result.metadata}\n\n"
                f"{raw_text}"
            )

        try:
            structured_md = self._llm.generate(
                system_prompt,
                user_prompt,
                model="gemini-flash",
                max_tokens=4096,
            )

            if not structured_md or len(structured_md.strip()) < 20:
                return None

            # Parse the structured markdown into sections
            sections = self._parse_markdown_to_sections(structured_md, extraction_result.title)

            logger.info(
                "K-01 structuring produced %d sections for %s",
                len(sections), extraction_result.title,
            )
            return {"title": extraction_result.title, "sections": sections}

        except Exception as e:
            logger.warning("K-01 LLM structuring failed: %s", e)
            return None

    @staticmethod
    def _parse_markdown_to_sections(markdown_text: str, default_title: str) -> list[dict]:
        """Parse structured markdown into sections list."""
        sections: list[dict] = []
        current_title = default_title
        current_depth = 1
        current_content: list[str] = []

        for line in markdown_text.split("\n"):
            if line.startswith("### "):
                if current_content:
                    content = "\n".join(current_content).strip()
                    if content:
                        sections.append({
                            "title": current_title, "content": content,
                            "page_start": None, "page_end": None, "depth": current_depth,
                        })
                current_title = line.lstrip("# ").strip()
                current_depth = 3
                current_content = []
            elif line.startswith("## "):
                if current_content:
                    content = "\n".join(current_content).strip()
                    if content:
                        sections.append({
                            "title": current_title, "content": content,
                            "page_start": None, "page_end": None, "depth": current_depth,
                        })
                current_title = line.lstrip("# ").strip()
                current_depth = 2
                current_content = []
            elif line.startswith("# "):
                if current_content:
                    content = "\n".join(current_content).strip()
                    if content:
                        sections.append({
                            "title": current_title, "content": content,
                            "page_start": None, "page_end": None, "depth": current_depth,
                        })
                current_title = line.lstrip("# ").strip()
                current_depth = 1
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            content = "\n".join(current_content).strip()
            if content:
                sections.append({
                    "title": current_title, "content": content,
                    "page_start": None, "page_end": None, "depth": current_depth,
                })

        return sections if sections else [{
            "title": default_title, "content": markdown_text,
            "page_start": None, "page_end": None, "depth": 1,
        }]

    # ================================================================
    # Step 1.7: 4-Tier PDF Structure Analysis
    # ================================================================

    # Regex patterns for structural title detection (Tier 3)
    _TITLE_PATTERNS = [
        # Chinese chapter/section markers
        (re.compile(r'^第[一二三四五六七八九十\d]+[章篇]'), 1),
        (re.compile(r'^第[一二三四五六七八九十\d]+[節节]'), 2),
        # Chinese ordinal markers (壹貳參...)
        (re.compile(r'^[壹貳參肆伍陸柒捌玖拾][\s、．.]'), 1),
        # Chinese parenthesized ordinals: （一）（二）...
        (re.compile(r'^（[一二三四五六七八九十]+）'), 2),
        (re.compile(r'^\([一二三四五六七八九十]+\)'), 2),
        # Numbered patterns: 1. / 1.1 / 1.1.1
        (re.compile(r'^\d+\.\d+\.\d+[\s\.、]'), 3),
        (re.compile(r'^\d+\.\d+[\s\.、]'), 2),
        (re.compile(r'^\d+\.[\s]'), 1),
        # Letter patterns: A. / (1)
        (re.compile(r'^[A-Z]\.[\s]'), 2),
        (re.compile(r'^\(\d+\)[\s]'), 3),
        # English chapter/section
        (re.compile(r'^Chapter\s+\d+', re.IGNORECASE), 1),
        (re.compile(r'^Section\s+\d+', re.IGNORECASE), 2),
        (re.compile(r'^Appendix\b', re.IGNORECASE), 1),
        # Chinese appendix
        (re.compile(r'^附錄'), 1),
    ]

    # Quiz/answer content detection patterns
    _QUIZ_PATTERNS = [
        re.compile(r'Ans[\s（(]?[A-Da-d][\s）)]'),
        re.compile(r'^\s*\([A-D]\)\s', re.MULTILINE),
        re.compile(r'^\s*（[A-D]）\s', re.MULTILINE),
        re.compile(r'^\s*\d+\.\s*\([A-D]\)', re.MULTILINE),
    ]

    def _analyze_pdf_structure(
        self, pdf_path: str, raw_sections: list[dict], doc_title: str
    ) -> list[dict] | None:
        """4-tier fallback strategy for PDF structure analysis.

        Tries each tier in order, returns structured sections from the first
        successful tier, or None if all fail (pipeline falls back to default).

        Tier 1: PDF bookmarks/outline (zero cost)
        Tier 2: LLM TOC extraction (1 API call)
        Tier 3: Regex title detection + cross-page merge (zero cost)
        Tier 4: Page-based + LLM batch naming (fallback)
        """
        # Build page_num → content map from raw sections
        page_map: dict[int, str] = {}
        for s in raw_sections:
            pn = s.get("page_start")
            if pn is not None:
                page_map[pn] = s.get("content", "")

        if not page_map:
            return None

        max_page = max(page_map.keys())

        # --- Tier 1: PDF Bookmarks ---
        result = self._tier1_bookmarks(pdf_path, page_map, max_page)
        if result:
            logger.info("PDF structure: Tier 1 (bookmarks) produced %d sections", len(result))
            return result

        # --- Tier 2: LLM TOC Extraction ---
        result = self._tier2_llm_toc(page_map, max_page, doc_title)
        if result:
            logger.info("PDF structure: Tier 2 (LLM TOC) produced %d sections", len(result))
            return result

        # --- Tier 3: Regex Title Detection ---
        result = self._tier3_regex_titles(page_map, max_page)
        if result:
            logger.info("PDF structure: Tier 3 (regex titles) produced %d sections", len(result))
            return result

        # --- Tier 4: LLM Batch Naming ---
        result = self._tier4_llm_batch_naming(raw_sections)
        if result:
            logger.info("PDF structure: Tier 4 (LLM batch naming) produced %d sections", len(result))
            return result

        logger.info("PDF structure: all tiers failed, using raw page sections")
        return None

    # --- Tier 1: PDF Bookmarks/Outline ---

    def _tier1_bookmarks(
        self, pdf_path: str, page_map: dict[int, str], max_page: int
    ) -> list[dict] | None:
        """Extract structure from PDF bookmarks/outline (TOC)."""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()  # list of [level, title, page_number]
            doc.close()
        except Exception as e:
            logger.debug("Tier 1: cannot read PDF TOC: %s", e)
            return None

        if not toc or len(toc) < 2:
            return None

        # Convert TOC entries to sections
        sections: list[dict] = []
        for i, entry in enumerate(toc):
            level, title, page_num = entry[0], entry[1], entry[2]
            if not title or not title.strip():
                continue

            # Determine page range: from this entry's page to next entry's page - 1
            if i + 1 < len(toc):
                page_end = toc[i + 1][2] - 1
                if page_end < page_num:
                    page_end = page_num
            else:
                page_end = max_page

            # Merge content from pages in range
            content = "\n\n".join(
                page_map[p] for p in range(page_num, page_end + 1) if p in page_map
            )

            if content.strip():
                depth = min(level, 3)  # cap at depth 3
                sections.append({
                    "title": title.strip()[:60],
                    "content": content,
                    "page_start": page_num,
                    "page_end": page_end,
                    "depth": depth,
                })

        return sections if len(sections) >= 2 else None

    # --- Tier 2: LLM TOC Extraction ---

    def _tier2_llm_toc(
        self, page_map: dict[int, str], max_page: int, doc_title: str
    ) -> list[dict] | None:
        """Send first 3 pages + last page to LLM to extract TOC structure."""
        if not self._llm:
            return None

        # Gather sample pages: first 3 + last
        sample_pages = sorted(page_map.keys())[:3]
        last_page = max(page_map.keys())
        if last_page not in sample_pages:
            sample_pages.append(last_page)

        sample_text = ""
        for pn in sample_pages:
            content = page_map.get(pn, "")[:1500]  # limit per page
            sample_text += f"\n--- 第 {pn} 頁 ---\n{content}\n"

        system_prompt = (
            "你是文件結構分析專家。根據提供的文件頁面（首3頁+末頁），推斷文件的目錄結構。\n"
            "回傳 JSON 格式，不要 markdown code block。\n"
            "如果無法判斷目錄結構（例如文件太短或無明顯章節），回傳 {\"chapters\": []}。\n\n"
            "使用語意階層萃取（Semantic Hierarchy Extraction）三層結構：\n"
            "  depth 1 = 核心主題（章）— 例如「信託法規」「No Code / Low Code 概念」\n"
            "  depth 2 = 次要概念（節）— 例如「信託契約要素」「生成式AI 應用領域」\n"
            "  depth 3 = 細節知識點（考點）— 例如「忠實義務範圍」「自動化行銷文案生成」\n\n"
            "格式範例：\n"
            '{"chapters": [\n'
            '  {"title": "第一章 概論", "page_start": 1, "page_end": 10, "depth": 1},\n'
            '  {"title": "1.1 背景", "page_start": 1, "page_end": 3, "depth": 2},\n'
            '  {"title": "1.1.1 歷史沿革", "page_start": 1, "page_end": 2, "depth": 3},\n'
            '  {"title": "1.2 目的", "page_start": 4, "page_end": 5, "depth": 2},\n'
            '  {"title": "第二章 方法", "page_start": 6, "page_end": 10, "depth": 1},\n'
            '  {"title": "練習題：第一章", "page_start": 11, "page_end": 12, "depth": 2, "type": "quiz"}\n'
            "]}\n\n"
            "規則：\n"
            "- title 要簡短（15字內），使用該主題的專業術語\n"
            "- 盡量產出 3 層結構（至少 2 層）\n"
            f"- 文件共 {max_page} 頁\n"
            "- 如果頁面內容主要是考題/選擇題，標記 type: quiz，標題加「練習題」前綴"
        )
        user_prompt = f"文件：{doc_title}\n{sample_text}"

        try:
            result = self._llm.generate(
                system_prompt,
                user_prompt,
                model="gemini-flash",
                max_tokens=4096,
            )
            parsed = self._parse_json_response(result)
            # 防禦：LLM 偶爾直接回傳 list（章節陣列）而非 {"chapters": [...]}
            if isinstance(parsed, list):
                chapters = parsed
            elif isinstance(parsed, dict):
                chapters = parsed.get("chapters", [])
            else:
                logger.warning("Tier 2: unexpected JSON type=%s", type(parsed).__name__)
                return None
            if not chapters:
                return None

            # Convert to sections with merged page content
            sections: list[dict] = []
            for ch in chapters:
                page_start = ch.get("page_start", 1)
                page_end = ch.get("page_end", page_start)
                depth = ch.get("depth", 1)
                title = ch.get("title", f"p.{page_start}")

                content = "\n\n".join(
                    page_map[p] for p in range(page_start, page_end + 1) if p in page_map
                )
                if content.strip():
                    sections.append({
                        "title": title.strip()[:60],
                        "content": content,
                        "page_start": page_start,
                        "page_end": page_end,
                        "depth": depth,
                        "chunk_type": "quiz" if ch.get("type") == "quiz" else "text",
                    })

            return sections if len(sections) >= 2 else None

        except Exception as e:
            logger.warning("Tier 2: LLM TOC extraction failed: %s", e)
            return None

    # --- Tier 3: Regex Title Detection + Cross-page Merge ---

    def _tier3_regex_titles(
        self, page_map: dict[int, str], max_page: int
    ) -> list[dict] | None:
        """Detect structural titles via regex, merge untitled pages into previous section."""
        # Scan each page for title patterns
        page_titles: dict[int, tuple[str, int]] = {}  # page_num → (title, depth)

        for pn in sorted(page_map.keys()):
            content = page_map[pn]
            # Check if page is primarily quiz content — mark but don't skip
            is_quiz = self._is_quiz_page(content)

            # Look at first 5 non-empty lines for title patterns
            lines = [l.strip() for l in content.split("\n") if l.strip()][:5]
            for line in lines:
                for pattern, depth in self._TITLE_PATTERNS:
                    if pattern.match(line):
                        # Use the matching line as title (truncate)
                        title = line[:60].rstrip("。，、；：")
                        if is_quiz:
                            title = f"{title}（練習題）"
                        page_titles[pn] = (title, depth)
                        break
                if pn in page_titles:
                    break

        if len(page_titles) < 2:
            return None

        # Build sections: pages with titles start new sections;
        # pages without titles merge UP into previous section
        sections: list[dict] = []
        current_title = None
        current_depth = 1
        current_pages: list[int] = []
        current_start = None

        for pn in sorted(page_map.keys()):
            if pn in page_titles:
                # Save previous section
                if current_title and current_pages:
                    content = "\n\n".join(
                        page_map[p] for p in current_pages if p in page_map
                    )
                    if content.strip():
                        sections.append({
                            "title": current_title,
                            "content": content,
                            "page_start": current_start,
                            "page_end": current_pages[-1],
                            "depth": current_depth,
                        })

                # Start new section
                current_title, current_depth = page_titles[pn]
                current_start = pn
                current_pages = [pn]
            else:
                if current_title:
                    # Merge into current section
                    current_pages.append(pn)
                else:
                    # No section yet — create an "intro" section
                    current_title = "前言"
                    current_depth = 1
                    current_start = pn
                    current_pages = [pn]

        # Don't forget the last section
        if current_title and current_pages:
            content = "\n\n".join(
                page_map[p] for p in current_pages if p in page_map
            )
            if content.strip():
                sections.append({
                    "title": current_title,
                    "content": content,
                    "page_start": current_start,
                    "page_end": current_pages[-1],
                    "depth": current_depth,
                })

        return sections if len(sections) >= 2 else None

    # --- Tier 4: Page-based + LLM Batch Naming ---

    def _tier4_llm_batch_naming(self, raw_sections: list[dict]) -> list[dict] | None:
        """Keep page-based splitting but ask LLM to generate semantic titles in batches."""
        if not self._llm:
            return None

        if not raw_sections:
            return None

        system_prompt = (
            "為以下文件段落各生成一個簡短的語義標題（15字以內）。\n"
            "使用該段落涵蓋的核心主題或專業術語作為標題，避免使用段落首句。\n"
            "如果段落主要是考題/選擇題，標題格式為「練習題：{主題}」。\n"
            "如果段落是答案解析，標題格式為「解答：{主題}」。\n"
            "回傳 JSON 陣列，每個元素是一個標題字串。\n"
            "不要 markdown code block，只回傳 JSON。\n"
            '範例：["No Code 基本概念","生成式AI 應用領域","練習題：第三章"]'
        )

        result_sections = list(raw_sections)  # copy
        batch_size = 10

        for batch_start in range(0, len(raw_sections), batch_size):
            batch = raw_sections[batch_start:batch_start + batch_size]

            # Build summaries for this batch
            summaries = []
            for i, s in enumerate(batch):
                content = s.get("content", "")
                preview = content[:200].replace("\n", " ").strip()
                page = s.get("page_start", "?")
                summaries.append(f"段落{batch_start + i + 1} (p.{page}): {preview}")

            user_prompt = "\n\n".join(summaries)

            try:
                response = self._llm.generate(
                    system_prompt,
                    user_prompt,
                    model="gemini-flash",
                    max_tokens=1024,
                )
                titles = json.loads(response.strip())
                if isinstance(titles, list):
                    for i, title in enumerate(titles):
                        idx = batch_start + i
                        if idx < len(result_sections) and isinstance(title, str) and title.strip():
                            result_sections[idx] = {
                                **result_sections[idx],
                                "title": title.strip()[:60],
                            }
            except Exception as e:
                logger.warning("Tier 4: LLM batch naming failed for batch %d: %s", batch_start, e)
                # Continue with remaining batches

        # Check if we got any meaningful titles
        meaningful = sum(
            1 for s in result_sections
            if not re.match(r'^p\.?\d+$', s.get("title", ""), re.IGNORECASE)
        )

        return result_sections if meaningful > 0 else None

    # --- Helper: Quiz page detection ---

    def _is_quiz_page(self, content: str) -> bool:
        """Detect if a page is primarily quiz/answer content."""
        matches = sum(
            len(pattern.findall(content)) for pattern in self._QUIZ_PATTERNS
        )
        # If 3+ quiz patterns found, it's likely a quiz page
        return matches >= 3

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
            # 嘗試從 DB 載入模板，fallback 到 hardcoded
            db_prompt = self._load_prompt("content_type_detect", {
                "doc_title": doc_title,
            })
            sys_prompt = db_prompt["system_prompt"] if db_prompt else STRUCTURE_ANALYSIS_PROMPT
            user_content = f"文件：{doc_title}\n\n" + "\n".join(summaries)

            # 由 LLMService routing 決定 provider（本地→Claude Code、雲端→API）
            result = self._llm.generate(
                sys_prompt,
                user_content,
                max_tokens=8000,
            )

            parsed = self._parse_json_response(result)
            # 防禦：LLM 偶爾直接回傳 list 而非 {"chapters": [...]}
            if isinstance(parsed, list):
                chapters = parsed
            elif isinstance(parsed, dict):
                chapters = parsed.get("chapters", [])
            else:
                logger.warning("AI structure analysis: unexpected JSON type=%s", type(parsed).__name__)
                return None
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
                                "title": sub.get("title") or f"p.{sub_page}",
                                "content": sub_content,
                                "page_start": sub_page, "page_end": sub_page,
                                "depth": 3, "parent_title": sec.get("title", ""),
                            })
                    else:
                        result.append({
                            "title": sec.get("title") or f"p.{sec_start}",
                            "content": sec_content,
                            "page_start": sec_start, "page_end": sec_end,
                            "depth": 2, "parent_title": ch.get("title", ""),
                        })
            else:
                # No sub-sections: chapter is a leaf
                result.append({
                    "title": ch.get("title") or f"p.{page_start}",
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
            chunk_type = section.get("chunk_type", "text")

            if len(tokens) <= chunk_size:
                # Section fits in a single chunk — keep it whole
                all_chunks.append({
                    "content": content, "token_count": len(tokens),
                    "source_page_start": page_start, "source_page_end": page_end,
                    "section_title": section_title, "depth": depth, "chunk_index": chunk_index,
                    "chunk_type": chunk_type,
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
                                "chunk_type": chunk_type,
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
                                    "chunk_type": chunk_type,
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
                        "chunk_type": chunk_type,
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

        import re
        _page_title_re = re.compile(r"^p\.?\d+$|^段落\s*\d+$|^第?\d+頁$|^page\s*\d+$", re.IGNORECASE)

        for i, section in enumerate(extracted.get("sections", [])):
            title = section.get("title", f"段落 {i + 1}")

            # If title is just a page number, derive a title from content instead
            if _page_title_re.match(title.strip()):
                content = section.get("content", "").strip()
                if not content:
                    continue  # Skip truly empty sections
                # Use first non-empty line (up to 30 chars) as title
                first_line = content.split("\n")[0].strip()[:30].rstrip("。，、；：")
                if not first_line or len(first_line) < 2:
                    continue
                title = first_line

            depth = section.get("depth", 1)
            parent_depth = depth - 1
            parent = parent_stack.get(parent_depth, root)

            node = KnowledgeNode(
                resource_id=resource.id,
                parent_id=parent.id,
                name=title,
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

            # 生成物理級跳轉錨點 ID
            page_start = cd.get("source_page_start")
            anchor_id = f"page_{page_start}" if page_start else f"chunk_{cd['chunk_index']}"

            # 計算高亮位置（基於 content 在原文中的行號）
            content_text = cd["content"]
            line_count = content_text.count("\n") + 1

            chunk = ResourceChunk(
                resource_id=resource.id, node_id=node_id,
                tenant_id=resource.tenant_id,
                chunk_index=cd["chunk_index"], content=content_text,
                token_count=cd["token_count"],
                source_page_start=page_start,
                source_page_end=cd.get("source_page_end"),
                anchor_id=anchor_id,
                highlight_line_start=cd.get("source_line_start"),
                highlight_line_end=cd.get("source_line_end"),
                highlight_char_start=cd.get("source_char_start"),
                highlight_char_end=cd.get("source_char_end"),
                metadata_json={
                    "section_title": cd.get("section_title", ""),
                    "depth": cd.get("depth", 1),
                    "chunk_type": cd.get("chunk_type", "text"),
                    "line_count": line_count,
                },
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
        """Delete original file after successful processing. Keep .md.

        使用 StorageService 統一刪除（本地/GCS 都支援）。
        注意：不再清空 gcs_path，保留以供後續溯源。
        YouTube 類型無檔案，跳過清理。
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
