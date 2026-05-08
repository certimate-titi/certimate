"""Resource LLM Parse Service — EPIC-035 核心後端 pipeline (TASK-035-04).

流程：
  1. API 層接到 POST /resources/{id}/parse
  2. check_and_consume 配額
  3. 建立 resource_parse_jobs row（status=queued）
  4. 背景任務呼叫 run_parse_job()
       a. fetch resource → download PDF to /tmp
       b. load prompt 'resource_parser_v2' from Feature 30 system
       c. call Gemini 2.5 Pro multimodal with PDF + prompt
       d. validate JSON output
       e. post-process:
            - persist parsed_markdown / parsed_text / detected_content_type
            - render WebP thumbnails + figures via resource_storage_service
            - T1 questions → questions 表
            - T2/T3 → question_candidates 表
            - scaffolds → resource_scaffolds 表
            - update resource_parse_jobs(finished, cost, tokens)
            - delete original PDF（由 lifecycle 兜底 7 天）

LLM 整合:
  - Gemini 2.5 Pro via `google.generativeai` SDK
  - File upload API for PDF
  - JSON mode response
  - Retry + exponential backoff（CTO 要求）

失敗處理:
  - LLM 超時/429 → exponential backoff (1s, 2s, 4s, 8s)
  - JSON schema 驗證失敗 → 記 failure_reason + mark failed
  - 原始 PDF 保留 7 天由 lifecycle 兜底 reparse
"""

from __future__ import annotations

import json
import re
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.question_candidate import (
    QuestionCandidate,
    QuestionCandidateTier,
)
from app.models.resource import Resource
from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-pro"
GEMINI_FLASH = "gemini-2.5-flash"  # fallback per CTO C2
MAX_RETRIES = 4
BASE_BACKOFF = 1.0  # seconds


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ParseOutcome:
    """Parse Outcome。"""
    job_id: UUID
    status: ParseJobStatus
    questions_created: int
    candidates_created: int
    scaffolds_created: int
    pages_rendered: int
    failure_reason: str | None = None


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def create_parse_job(db: Session, resource: Resource) -> ResourceParseJob:
    """建立 queued job（由 API 層呼叫，同步）。"""
    job = ResourceParseJob(
        resource_id=resource.id,
        tenant_id=resource.tenant_id,
        status=ParseJobStatus.QUEUED.value,
        gemini_model=GEMINI_MODEL,
    )
    db.add(job)
    db.flush()
    return job


def run_parse_job(db: Session, job_id: UUID) -> ParseOutcome:
    """背景執行。由 FastAPI BackgroundTasks 或 job queue 呼叫。"""
    job: ResourceParseJob | None = db.get(ResourceParseJob, job_id)
    if job is None:
        raise ValueError(f"parse job not found: {job_id}")

    resource: Resource | None = db.get(Resource, job.resource_id)
    if resource is None:
        _fail(db, job, "resource not found")
        return ParseOutcome(job.id, ParseJobStatus.FAILED, 0, 0, 0, 0, "resource missing")

    job.status = ParseJobStatus.PARSING.value
    job.started_at = datetime.now(timezone.utc)
    db.flush()

    try:
        parsed = _call_gemini_with_retry(resource)
    except Exception as exc:  # noqa: BLE001
        logger.exception("gemini call failed resource=%s", resource.id)
        _fail(db, job, f"gemini error: {exc}")
        return ParseOutcome(job.id, ParseJobStatus.FAILED, 0, 0, 0, 0, str(exc))

    try:
        outcome = _persist_parsed(db, resource, job, parsed)
    except Exception as exc:  # noqa: BLE001
        logger.exception("persist parsed failed resource=%s", resource.id)
        _fail(db, job, f"persist error: {exc}")
        return ParseOutcome(job.id, ParseJobStatus.FAILED, 0, 0, 0, 0, str(exc))

    job.status = ParseJobStatus.SUCCESS.value
    job.finished_at = datetime.now(timezone.utc)
    job.detected_content_type = parsed.get("detected_content_type")
    job.critical_pages = parsed.get("critical_pages", []) or []
    db.flush()

    return outcome


# ---------------------------------------------------------------------------
# Gemini integration
# ---------------------------------------------------------------------------

PAGE_THRESHOLD_FOR_BATCHING = 30
BATCH_SIZE_PAGES = 25


def _call_gemini_with_retry(resource: Resource) -> dict[str, Any]:
    """智慧分流：≤30 頁直接 multimodal，>30 頁切批並行（D 方案）。

    - 小 PDF 保留 multimodal Pro 對掃描型/特殊編碼 PDF 的視覺辨識能力
    - 大 PDF 切 25 頁/批，避免 32K output token 上限導致 markdown 截斷為空
    """
    logger.info(
        "[D-dispatch] _call_gemini_with_retry entry resource=%s gcs_path=%s",
        resource.id, bool(resource.gcs_path),
    )
    page_count = 0
    local_pdf: str | None = None
    if resource.gcs_path:
        try:
            from app.services.storage_service import get_storage_service
            local_pdf = get_storage_service().download_to_temp(resource.gcs_path)
            page_count = _get_pdf_page_count(local_pdf)
            logger.info(
                "[D-dispatch] resource=%s page_count=%d threshold=%d",
                resource.id, page_count, PAGE_THRESHOLD_FOR_BATCHING,
            )
        except Exception as exc:
            logger.warning("[D-dispatch] PDF page count failed (will use single call): %s", exc)

    if page_count > 0 and page_count > PAGE_THRESHOLD_FOR_BATCHING and local_pdf:
        logger.info(
            "[D-dispatch] PDF batched parse: pages=%d batch_size=%d resource=%s",
            page_count, BATCH_SIZE_PAGES, resource.id,
        )
        return _call_gemini_chunked(resource, local_pdf, BATCH_SIZE_PAGES)

    logger.info("[D-dispatch] using single-call path resource=%s", resource.id)
    return _call_gemini_with_retry_single(resource)


def _call_gemini_with_retry_single(resource: Resource) -> dict[str, Any]:
    """單一 multimodal 呼叫 + retry + Flash fallback（原邏輯）。"""
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return _call_gemini_once(resource, model=GEMINI_MODEL)
        except _RetryableError as e:
            last_exc = e
            wait = BASE_BACKOFF * (2 ** attempt)
            logger.warning(
                "gemini retryable error attempt=%d wait=%.1fs: %s",
                attempt + 1, wait, e,
            )
            time.sleep(wait)
        except Exception:
            raise

    # fallback to Flash if Pro exhausted retries
    logger.warning("falling back to Gemini Flash after exhausting Pro retries")
    try:
        return _call_gemini_once(resource, model=GEMINI_FLASH)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"gemini exhausted retries + flash fallback; last_err={last_exc} final_err={exc}"
        ) from exc


def _call_gemini_chunked(
    resource: Resource, local_pdf: str, batch_size: int,
) -> dict[str, Any]:
    """大 PDF 切批並行 multimodal Pro 解析後 merge。

    每批失敗不影響其他；至少有 1 批成功 markdown 就算有效。
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import os as _os

    batch_paths = _split_pdf_pages(local_pdf, batch_size=batch_size)
    logger.info("split into %d batches resource=%s", len(batch_paths), resource.id)

    parts: list[dict[str, Any]] = []
    success = 0

    def _run_batch(batch_path: str, model: str) -> dict[str, Any]:
        """單批呼叫 + retry + Flash fallback（同 _call_gemini_with_retry_single 邏輯
        但傳 local_pdf_override）。"""
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                return _call_gemini_once(resource, model=GEMINI_MODEL, local_pdf_override=batch_path)
            except _RetryableError as e:
                last_exc = e
                time.sleep(BASE_BACKOFF * (2 ** attempt))
            except Exception:
                raise
        # Flash fallback
        try:
            return _call_gemini_once(resource, model=GEMINI_FLASH, local_pdf_override=batch_path)
        except Exception as exc:
            raise RuntimeError(f"batch retries exhausted; last={last_exc} final={exc}") from exc

    with ThreadPoolExecutor(max_workers=min(4, len(batch_paths))) as ex:
        futures = {}
        for i, bp in enumerate(batch_paths):
            offset = i * batch_size
            futures[ex.submit(_run_batch, bp, GEMINI_MODEL)] = (i, bp, offset)
        for fut in as_completed(futures):
            i, bp, offset = futures[fut]
            try:
                result = fut.result()
                _shift_page_numbers(result, offset)
                parts.append(result)
                success += 1
                logger.info(
                    "batch %d done resource=%s md_len=%d",
                    i, resource.id, len(result.get("markdown") or ""),
                )
            except Exception as exc:
                logger.warning(
                    "batch %d failed resource=%s: %s",
                    i, resource.id, exc,
                )

    # 清掉 batch tempfiles
    for bp in batch_paths:
        try:
            _os.unlink(bp)
        except Exception:
            pass

    if success == 0:
        raise RuntimeError(f"all {len(batch_paths)} batches failed for resource={resource.id}")

    return _merge_parsed_results(parts)


def _shift_page_numbers(parsed: dict[str, Any], offset: int) -> None:
    """把 batch-local 頁碼（1-N）+offset 還原為全域 PDF 頁碼。"""
    if not isinstance(parsed, dict) or offset == 0:
        return
    # critical_pages（容錯 dict / str）
    shifted_pages = []
    for p in (parsed.get("critical_pages") or []):
        if isinstance(p, int):
            shifted_pages.append(p + offset)
        elif isinstance(p, dict):
            for key in ("page", "page_number", "p"):
                if isinstance(p.get(key), int):
                    p[key] = p[key] + offset
                    shifted_pages.append(p[key])
                    break
        elif isinstance(p, str) and p.isdigit():
            shifted_pages.append(int(p) + offset)
    parsed["critical_pages"] = shifted_pages
    # questions[].source_page
    for q in parsed.get("questions") or []:
        if isinstance(q, dict) and isinstance(q.get("source_page"), int):
            q["source_page"] = q["source_page"] + offset
    # markdown 中的 FIGURE:pN_iM 也要 shift
    md = parsed.get("markdown") or ""
    if md:
        def _shift(m):
            n = int(m.group(1))
            idx = m.group(2)
            return f"![圖](FIGURE:p{n + offset}_i{idx})"
        parsed["markdown"] = re.sub(r"!\[圖\]\(FIGURE:p(\d+)_i(\d+)\)", _shift, md)


class _RetryableError(Exception):
    """_ Retryable Error 例外類別。"""
    pass


def _get_pdf_page_count(pdf_path: str) -> int:
    """快速讀 PDF 頁數（PyMuPDF）。"""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        n = len(doc)
        doc.close()
        logger.info("_get_pdf_page_count: pdf_path=%s pages=%d", pdf_path, n)
        return n
    except Exception as exc:
        logger.warning("_get_pdf_page_count failed pdf_path=%s: %s", pdf_path, exc)
        return 0


def _split_pdf_pages(pdf_path: str, batch_size: int = 25) -> list[str]:
    """切 PDF 為多個 batch_size 頁的小 PDF，回 tempfile 路徑陣列。

    對 60+ 頁 PDF 解 max_output_tokens 上限：每批小於 25 頁
    → markdown 預期 < 15K tokens 安全在 32K 內。
    """
    import tempfile
    import fitz
    out_paths: list[str] = []
    src = fitz.open(pdf_path)
    total = len(src)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_doc = fitz.open()
        batch_doc.insert_pdf(src, from_page=start, to_page=end - 1)
        with tempfile.NamedTemporaryFile(prefix=f"batch_p{start+1}-{end}_", suffix=".pdf", delete=False) as f:
            batch_doc.save(f.name)
            out_paths.append(f.name)
        batch_doc.close()
    src.close()
    return out_paths


def _merge_parsed_results(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """合併 N 批 Gemini 結果為單一 parsed dict。"""
    merged_md: list[str] = []
    questions: list[dict] = []
    scaffolds: list[dict] = []
    critical_pages: list[int] = []
    detected_types: list[str] = []
    for p in parts:
        if not isinstance(p, dict):
            continue
        md = p.get("markdown") or ""
        if md:
            merged_md.append(md)
        questions.extend(p.get("questions") or [])
        scaffolds.extend(p.get("scaffolds") or [])
        # critical_pages 容錯：Gemini 偶爾回 dict（{"page": N, "reason": ...}）
        # 不是純 int。提取數字部分，丟掉異常型別。
        for cp in (p.get("critical_pages") or []):
            if isinstance(cp, int):
                critical_pages.append(cp)
            elif isinstance(cp, dict):
                v = cp.get("page") or cp.get("page_number") or cp.get("p")
                if isinstance(v, int):
                    critical_pages.append(v)
            elif isinstance(cp, str) and cp.isdigit():
                critical_pages.append(int(cp))
        if p.get("detected_content_type"):
            detected_types.append(p["detected_content_type"])
    # detected_content_type 取多數派；critical_pages 去重保序
    seen: set = set()
    unique_pages: list[int] = []
    for p in critical_pages:
        if p not in seen:
            seen.add(p)
            unique_pages.append(p)
    return {
        "markdown": "\n\n".join(merged_md),
        "detected_content_type": (
            max(set(detected_types), key=detected_types.count) if detected_types else None
        ),
        "critical_pages": unique_pages,
        "questions": questions,
        "scaffolds": scaffolds,
    }


def _select_prompt_template(resource: Resource) -> str:
    """Sprint 2 P1 T18：依檔案類型 / 內容類型選 prompt template 名稱。

    路由規則（順序敏感）：
      1. 影片副檔名（mp4/mov/avi/mkv/webm）→ resource_parser_video
      2. YouTube URL → resource_parser_video
      3. detected_content_type=practice_questions → resource_parser_quiz
      4. 預設 → resource_parser_v2（K-06-study，原有 prompt）

    所有特化模板若 DB 不存在會 fallback 到 resource_parser_v2，避免阻斷流程。

    Args:
        resource: Resource ORM row

    Returns:
        prompt template name（不含路徑或檔案副檔名）
    """
    ext = ""
    if resource.gcs_path:
        ext = resource.gcs_path.lower().rsplit(".", 1)[-1] if "." in resource.gcs_path else ""

    # 1) Video by extension
    if ext in {"mp4", "mov", "avi", "mkv", "webm", "m4v"}:
        return "resource_parser_video"

    # 2) YouTube URL
    if getattr(resource, "youtube_url", None):
        return "resource_parser_video"

    # 3) PPT slides (Sprint 3 P2)
    if ext in {"ppt", "pptx"}:
        return "resource_parser_slides"

    # 4) DOCX personal notes (Sprint 3 P2)
    if ext in {"doc", "docx"}:
        return "resource_parser_notes"

    # 5) Audio (Sprint 4 P3)
    if ext in {"mp3", "wav", "m4a", "flac", "ogg", "wma", "aac"}:
        return "resource_parser_audio"

    # 6) Image (Sprint 4 P3)
    if ext in {"png", "jpg", "jpeg", "gif", "webp"}:
        return "resource_parser_image"

    # 7) Quiz / practice questions
    detected = getattr(resource, "detected_content_type", None)
    if detected == "practice_questions":
        return "resource_parser_quiz"

    # 8) Default: K-06-study
    return "resource_parser_v2"


def _call_gemini_once(
    resource: Resource, model: str, local_pdf_override: str | None = None,
) -> dict[str, Any]:
    """實際呼叫 Gemini。

    為避免在 import 時需要 google.generativeai，這裡 lazy import。
    測試可透過 monkeypatch 這個函式或塞 fake。

    Args:
        local_pdf_override: 若提供，跳過 storage.download_to_temp，直接用該本地路徑。
                            用於 D 方案 batch 模式（傳已切好的 batch PDF）。
    """
    try:
        from google import genai
    except ImportError as e:
        raise RuntimeError("google-genai SDK not installed") from e

    from app.core.config import get_settings
    from app.services.storage_service import get_storage_service
    from app.services.prompt_template_service import PromptTemplateService

    settings = get_settings()
    api_key = (
        getattr(settings, "GEMINI_API_KEY", None)
        or getattr(settings, "gemini_api_key", None)
        or ""
    )
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")
    client = genai.Client(api_key=api_key)

    # P1 (Sprint 2 T18)：依檔案類型 / 內容類型分流選 prompt template
    template_name = _select_prompt_template(resource)
    logger.info(
        "[prompt-routing] resource=%s template=%s ext=%s detected=%s",
        resource.id, template_name,
        (resource.gcs_path or '').lower().rsplit('.', 1)[-1] if resource.gcs_path else '?',
        getattr(resource, 'detected_content_type', None),
    )
    template = None
    try:
        from app.core.deps import _SessionLocal
        if _SessionLocal is not None:
            _tmp_db = _SessionLocal()
            try:
                prompt_service = PromptTemplateService(_tmp_db)
                template = prompt_service.get_prompt_for_ai(template_name)
                # fallback 到 K-06-study (resource_parser_v2) 若特化模板不存在
                if template is None and template_name != "resource_parser_v2":
                    logger.warning(
                        "prompt template '%s' not found, fallback to resource_parser_v2",
                        template_name,
                    )
                    template = prompt_service.get_prompt_for_ai("resource_parser_v2")
            finally:
                _tmp_db.close()
    except Exception as _e:
        logger.warning("prompt template lookup failed: %s", _e)
        template = None
    def _tget(obj, key):
        """ tget。"""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    system_prompt = (
        _tget(template, "system_prompt")
        or "（fallback）將資源解析為 Output Contract 指定的 JSON。"
    )
    raw_user_prompt = _tget(template, "user_prompt") or ""
    if raw_user_prompt:
        user_prompt = raw_user_prompt
        for var, val in (
            ("filename", resource.name),
            ("source_type", resource.source_type or "user_other"),
            ("declared_exam_code", resource.exam_code or ""),
        ):
            user_prompt = user_prompt.replace("{" + var + "}", str(val))
    else:
        user_prompt = (
            "請將此 PDF 解析為符合 Output Contract 的 JSON，"
            f"檔名={resource.name}。"
        )

    # 強制 schema 鎖定（防 Gemini 把文件內容的目錄結構當任務 schema 用）
    # 觀察：「AI規劃師學習指引」內含 chapters/references/job_profile 段落，
    # 之前 Gemini 會直接套用文件本身的 schema 回應，導致 scaffolds=0
    schema_hammer = (
        "\n\n# ⚠️ JSON SCHEMA 強制鎖定（最高優先）\n"
        "你的 JSON 物件 **頂層 keys 必須且只能是**：\n"
        '`markdown`, `detected_content_type`, `critical_pages`, `questions`, `scaffolds`\n\n'
        "**禁止頂層出現** `document_title`, `issuer`, `chapters`, `curriculum`, "
        "`references`, `job_profile` 或任何文件本身的目錄欄位。\n"
        "若 PDF 看似一份「學習指引／簡章／目錄」，其章節結構應放入 `scaffolds[].chapter_heading`，\n"
        "**不**能取代頂層 schema。\n\n"
        "# scaffolds 內每筆物件必填欄位（缺一即無效會被丟棄）\n"
        "- `chapter_heading`: string（章節標題）\n"
        "- `type`: **必須是** `takeaway` | `elaborative` | `strategy` 三選一（小寫，不接受 null / 空字串 / 其他值）\n"
        "- `content`: string（鷹架內文）\n"
        "至少為文件中前 10 個有意義的章節各產出 takeaway + elaborative + strategy 三筆，"
        "預期 scaffolds 陣列長度 30+ 而非個位數。"
    )
    user_prompt = user_prompt + schema_hammer

    # download PDF locally for upload (or use override for batch mode)
    if local_pdf_override:
        local_pdf = local_pdf_override
    else:
        storage = get_storage_service()
        if not resource.gcs_path:
            raise RuntimeError("resource has no gcs_path")
        local_pdf = storage.download_to_temp(resource.gcs_path)

    ext = (resource.gcs_path or resource.name or "").lower().rsplit(".", 1)[-1]
    if local_pdf_override:
        ext = "pdf"  # batch 必為 pdf

    # Workaround: Gemini SDK 上傳檔名含中文時觸發 'ascii' codec error。
    # 複製到 ASCII-named tempfile 後再上傳。
    import tempfile, shutil, os as _os
    try:
        local_pdf.encode("ascii")
        ascii_path = local_pdf  # 已是純 ASCII
        ascii_temp = None
    except UnicodeEncodeError:
        suffix = f".{ext}" if ext and len(ext) <= 5 else ".bin"
        with tempfile.NamedTemporaryFile(prefix="parse_", suffix=suffix, delete=False) as dst:
            with open(local_pdf, "rb") as src:
                shutil.copyfileobj(src, dst)
            ascii_path = dst.name
        ascii_temp = ascii_path
        logger.info(f"copied non-ascii filename to {ascii_path} for Gemini upload")
    mime_map = {
        "pdf": "application/pdf",
        "md": "text/markdown",
        "markdown": "text/markdown",
        "txt": "text/plain",
        "html": "text/html",
        "htm": "text/html",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }
    mime = mime_map.get(ext, "application/pdf")

    try:
        uploaded = client.files.upload(
            file=ascii_path,
            config={"mime_type": mime},
        )
        resp = client.models.generate_content(
            model=model,
            contents=[uploaded, user_prompt],
            config={
                "system_instruction": system_prompt,
                "temperature": 0.1,
                "response_mime_type": "application/json",
                # 不設此欄 SDK 預設 8192，會把長表格 / 100 條清單 markdown 截斷
                # （症狀：6949 chars 後突然停在第 4 列）。Gemini 2.5 Pro 上限 65536。
                "max_output_tokens": 65536,
            },
        )
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        if "429" in msg or "quota" in msg or "timeout" in msg or "unavailable" in msg:
            raise _RetryableError(str(e)) from e
        raise
    finally:
        # 清掉 ASCII tempfile（如果有建）
        if ascii_temp:
            try:
                _os.unlink(ascii_temp)
            except Exception:
                pass

    text = getattr(resp, "text", None) or ""
    # RC19 修補（2026-04-30）：Gemini 偶爾回 JSON 但 markdown 字串內含
    # unescaped 控制字元（裸 \n / \t），strict mode 拒絕 → 改用 strict=False。
    # 順帶移除可能的 markdown code fence（```json ... ```）
    text_to_parse = text.strip()
    if text_to_parse.startswith("```"):
        # 移除 ```json 或 ``` 開頭、``` 結尾
        text_to_parse = re.sub(r"^```(?:json)?\s*\n?", "", text_to_parse, flags=re.IGNORECASE)
        text_to_parse = re.sub(r"\n?```\s*$", "", text_to_parse)
    try:
        parsed = json.loads(text_to_parse, strict=False)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"gemini returned non-JSON: {text_to_parse[:500]}") from e
    if isinstance(parsed, dict):
        logger.info(
            "parse result resource=%s questions=%d scaffolds=%d md_len=%d",
            resource.id,
            len(parsed.get("questions") or []),
            len(parsed.get("scaffolds") or []),
            len(parsed.get("markdown") or ""),
        )
    return parsed


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _persist_parsed(
    db: Session,
    resource: Resource,
    job: ResourceParseJob,
    parsed: dict[str, Any],
) -> ParseOutcome:
    # 1) resources.* fields
    """儲存 parsed。"""
    raw_markdown = parsed.get("markdown") or ""
    # 守門：若 Gemini Pro 回空 markdown（大 PDF 超 token / 解析失敗等），
    # 不要覆蓋 Step 2 已寫的 markdown（chunks 可能仍有合理內容）。
    # 這對 60+ 頁 PDF 特別重要，Pro 多模態常因 token 上限回空 / 截斷 JSON。
    if not raw_markdown.strip():
        logger.warning(
            "parse markdown is empty resource=%s — skip overwrite to preserve Step 2 markdown",
            resource.id,
        )
        resource.detected_content_type = parsed.get("detected_content_type") or resource.detected_content_type
        # 仍回 outcome；不寫 parsed_markdown（保留先前值）
        return ParseOutcome(
            job_id=job.id,
            status=ParseJobStatus.SUCCESS,
            questions_created=0,
            candidates_created=0,
            scaffolds_created=0,
            pages_rendered=0,
        )
    resource.detected_content_type = parsed.get("detected_content_type")

    # 2) WebP + figures — dispatch to resource_storage_service（critical pages aware）
    pages_rendered = 0
    figure_url_map: dict[str, str] = {}  # "p3_i0" → public URL
    try:
        from app.services.resource_storage_service import render_pdf_to_webp
        from app.services.storage_service import get_storage_service

        storage = get_storage_service()
        if resource.gcs_path:
            local_pdf = storage.download_to_temp(resource.gcs_path)
            critical = set(parsed.get("critical_pages") or [])
            results = render_pdf_to_webp(
                pdf_path=local_pdf,
                user_id=str(resource.user_id),
                resource_id=str(resource.id),
                critical_pages=critical,
            )
            pages_rendered = len(results)
            # 建立 figure_id → public URL 對照表（替換 markdown 佔位符用）
            for page_result in results:
                for fig_path in (page_result.figures or []):
                    fname = fig_path.rsplit("/", 1)[-1]  # e.g. "p3_i0.png"
                    fig_id = fname.rsplit(".", 1)[0]      # e.g. "p3_i0"
                    try:
                        figure_url_map[fig_id] = storage.to_public_url(fig_path)
                    except Exception:
                        logger.warning(
                            "to_public_url failed resource=%s fig=%s",
                            resource.id, fig_id, exc_info=True,
                        )
    except Exception:
        logger.warning("webp render failed resource=%s", resource.id, exc_info=True)

    # 3) 替換 markdown 中圖片佔位符 ![圖](FIGURE:p3_i0) → ![圖](https://gcs/...)
    import re as _re
    def _sub(m):
        fid = m.group(1)
        return f"![圖]({figure_url_map.get(fid, '')})" if figure_url_map.get(fid) else ""
    final_markdown = _re.sub(r"!\[圖\]\(FIGURE:(p\d+_i\d+)\)", _sub, raw_markdown)
    resource.parsed_markdown = final_markdown
    resource.parsed_text = _extract_plain_text(final_markdown)

    # 3) questions / candidates / scaffolds
    q_created = 0
    c_created = 0
    s_created = 0

    for q in parsed.get("questions", []) or []:
        tier = (q.get("tier") or "").upper()
        if tier == "T1":
            db.add(_build_question_row(resource, q))
            q_created += 1
        elif tier in ("T2", "T3"):
            db.add(_build_candidate_row(resource, q, tier))
            c_created += 1

    new_scaffold_rows: list[ResourceScaffold] = []
    # P1 (Sprint 2 T14)：dedup pitfall — 同 (chapter, type=pitfall) 只保留一筆
    # （prompt 規則「每章節 0-1 條」，但 LLM 偶爾會重複）
    seen_pitfall_chapters: set[str] = set()
    for s in parsed.get("scaffolds", []) or []:
        if (s.get("type") or "").lower() == "pitfall":
            ch = (s.get("chapter_heading") or "").strip()
            if ch and ch in seen_pitfall_chapters:
                logger.info(
                    "[pitfall-dedup] skip duplicate pitfall in chapter=%r resource=%s",
                    ch[:30], resource.id,
                )
                continue
            if ch:
                seen_pitfall_chapters.add(ch)
        row = _build_scaffold_row(resource, s)
        if row is not None:
            db.add(row)
            new_scaffold_rows.append(row)
            s_created += 1

    db.flush()

    # 3b) elaborative 類鷹架預產 AI 參考答案（TASK-03）
    _generate_reference_answers(new_scaffold_rows)
    db.flush()

    # 3c) P6 (Sprint 7 T54)：voyage embedding 持久化（省後續 /concept-center cost）
    _embed_scaffolds(new_scaffold_rows)
    db.flush()

    # 4) 映射 T1 題目到科目知識節點（Voyage cosine similarity）
    if q_created > 0 and resource.subject_id:
        try:
            _map_questions_to_nodes(db, resource)
        except Exception:
            logger.warning(
                "node mapping failed resource=%s", resource.id, exc_info=True
            )

    return ParseOutcome(
        job_id=job.id,
        status=ParseJobStatus.SUCCESS,
        questions_created=q_created,
        candidates_created=c_created,
        scaffolds_created=s_created,
        pages_rendered=pages_rendered,
    )


def _map_questions_to_nodes(db: Session, resource: Resource) -> int:
    """將本次解析的 T1 題目用 Voyage embedding 映射到 subject 的知識節點。"""
    import math

    from sqlalchemy import text  # RC20: 補漏 import 修 NameError
    from app.services.embedding_service import EmbeddingService

    nodes = db.execute(
        text(
            """
            SELECT id, name, COALESCE(source_text, name)
            FROM knowledge_nodes WHERE subject_id = :sid
            """
        ),
        {"sid": resource.subject_id},
    ).fetchall()
    if not nodes:
        logger.info("no nodes in subject=%s, skip mapping", resource.subject_id)
        return 0

    qs = db.execute(
        text(
            """
            SELECT id, content, option_a, option_b, option_c, option_d
            FROM questions
            WHERE source_resource_id = :rid AND node_id IS NULL
            """
        ),
        {"rid": resource.id},
    ).fetchall()
    if not qs:
        return 0

    emb = EmbeddingService()
    node_texts = [f"{r[1]} — {(r[2] or '')[:400]}" for r in nodes]
    q_texts = [" ".join(str(c or "") for c in r[1:6])[:500] for r in qs]
    node_embs = emb.embed_texts(node_texts, input_type="document")
    q_embs = emb.embed_texts(q_texts, input_type="document")
    node_ids = [r[0] for r in nodes]

    def _cos(a: list, b: list) -> float:
        """ cos。"""
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)

    mapped = 0
    for qi, qe in enumerate(q_embs):
        best_i = max(range(len(node_embs)), key=lambda i: _cos(qe, node_embs[i]))
        db.execute(
            text("UPDATE questions SET node_id = :nid WHERE id = :qid"),
            {"nid": node_ids[best_i], "qid": qs[qi][0]},
        )
        mapped += 1
    logger.info(
        "mapped %d questions to nodes resource=%s nodes=%d",
        mapped,
        resource.id,
        len(nodes),
    )
    return mapped


def _build_question_row(resource: Resource, q: dict[str, Any]) -> Question:
    """建立 question row。"""
    opts = q.get("options") or []
    def _opt(i: int) -> str | None:
        """ opt。"""
        return opts[i] if i < len(opts) else None

    needs_answer = bool(q.get("needs_answer"))
    confidence = q.get("confidence")
    row = Question(
        content=q.get("question_text") or "",
        option_a=_opt(0),
        option_b=_opt(1),
        option_c=_opt(2),
        option_d=_opt(3),
        correct_answer=(q.get("answer") or q.get("ai_inferred_answer") or "?"),
        explanation=q.get("explanation") or q.get("inference_reasoning"),
        source_resource_id=resource.id,
        owner_user_id=resource.user_id,  # M4 個人題庫 scope
        source_type="user_upload",
        tenant_id=resource.tenant_id,
        answer_source="authoritative" if q.get("answer") else "ai_inferred",
        confidence=confidence,
        needs_answer=needs_answer,
        never_for_scoring=(
            needs_answer or (confidence is not None and confidence < 0.9)
        ),
        question_number=q.get("source_page") or 0,
    )
    return row


def _build_candidate_row(
    resource: Resource, q: dict[str, Any], tier: str
) -> QuestionCandidate:
    """建立 candidate row。"""
    return QuestionCandidate(
        resource_id=resource.id,
        tenant_id=resource.tenant_id,
        question_text=q.get("question_text") or "",
        options=q.get("options") or [],
        ai_inferred_answer=q.get("ai_inferred_answer") or q.get("answer"),
        confidence=q.get("confidence"),
        source_page=q.get("source_page"),
        figure_refs=q.get("figure_refs") or [],
        tier=QuestionCandidateTier(tier).value,
    )


def _build_scaffold_row(
    resource: Resource, s: dict[str, Any]
) -> ResourceScaffold | None:
    """建立 scaffold row。"""
    raw_type = (s.get("type") or "").lower()
    try:
        t = ResourceScaffoldType(raw_type)
    except ValueError:
        logger.warning(
            "scaffold dropped (invalid type=%r) resource=%s heading=%r",
            s.get("type"), resource.id, (s.get("chapter_heading") or "")[:30]
        )
        return None
    page_start, page_end = _coerce_page_range(s)
    # P0 (Sprint 1 T04)：寫入 retrieval_prompt（K-06 v3 schema）
    # takeaway 必填、elaborative 可選、strategy 不需要
    retrieval_prompt = s.get("retrieval_prompt")
    if retrieval_prompt is not None and not isinstance(retrieval_prompt, str):
        retrieval_prompt = None
    if retrieval_prompt and not retrieval_prompt.strip():
        retrieval_prompt = None
    return ResourceScaffold(
        resource_id=resource.id,
        tenant_id=resource.tenant_id,
        chapter_heading=s.get("chapter_heading"),
        type=t.value,
        content=s.get("content") or "",
        page_start=page_start,
        page_end=page_end,
        retrieval_prompt=retrieval_prompt,
        template_code="K-06-study",
    )


def _embed_scaffolds(rows: list[ResourceScaffold]) -> None:
    """P6 (Sprint 7 T54)：寫入 voyage embedding 給 /concept-center 語意搜尋用。

    對 chapter_heading + content 做 embedding，存入 resource_scaffolds.embedding 欄。

    失敗不阻斷：voyage API 異常時 embedding 留 NULL，
    /concept-center 會 fallback 即時 embed（行為等同 Sprint 6 T49）。
    """
    if not rows:
        return
    try:
        from app.services.embedding_service import EmbeddingService
        emb = EmbeddingService()
        texts = [
            ((r.chapter_heading or "") + " " + (r.content or "")).strip()[:1000]
            for r in rows
        ]
        vecs = emb.embed_texts(texts, input_type="document")
        for row, vec in zip(rows, vecs):
            row.embedding = vec
        logger.info("[scaffold-embed] %d rows embedded", len(rows))
    except Exception as e:
        logger.warning("[scaffold-embed] failed (non-fatal): %s", e)


def _generate_reference_answers(rows: list[ResourceScaffold]) -> None:
    """為 elaborative 類鷹架預產 AI 參考答案（TASK-03）。

    失敗不阻斷解析流程：單筆失敗只記 warning，rows 的 reference_answer 留 None。
    測試環境可 monkeypatch `_call_gemini_reference_answer` 注入 fake。
    """
    for row in rows:
        type_val = row.type.value if hasattr(row.type, "value") else row.type
        if type_val != ResourceScaffoldType.ELABORATIVE.value:
            continue
        if not row.content:
            continue
        try:
            answer = _call_gemini_reference_answer(row.content, row.chapter_heading)
        except Exception:
            logger.warning(
                "reference answer generation failed scaffold_id=%s",
                row.id, exc_info=True,
            )
            continue
        if answer:
            row.reference_answer = answer


def _call_gemini_reference_answer(question: str, chapter_heading: str | None) -> str | None:
    """呼叫 Gemini 產生延伸思考題的參考答案。

    使用 Flash（速度優先、批次生成、每資源數張鷹架）。
    """
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        raise RuntimeError("google-genai SDK not installed")

    from app.core.config import get_settings

    settings = get_settings()
    api_key = (
        getattr(settings, "GEMINI_API_KEY", None)
        or getattr(settings, "gemini_api_key", None)
        or ""
    )
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    client = genai.Client(api_key=api_key)
    heading_line = f"章節：{chapter_heading}\n" if chapter_heading else ""
    prompt = (
        "你是一位證照考試輔導老師。請針對以下延伸思考題給一段簡潔的參考答案，"
        "長度 100–200 字，聚焦考試重點，避免冗詞。\n\n"
        f"{heading_line}題目：{question}\n\n參考答案："
    )

    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.models.generate_content(
                model=GEMINI_FLASH,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=512,
                ),
            )
            return (getattr(resp, "text", None) or "").strip() or None
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(BASE_BACKOFF * (2 ** attempt))
    if last_exc is not None:
        raise last_exc
    return None


def _coerce_page_range(s: dict[str, Any]) -> tuple[int | None, int | None]:
    """從鷹架 payload 解析 page_start / page_end。

    LLM 可能用不同形狀回傳：顯式 page_start/page_end、單一 source_page、
    或 pages: [start, end]。都歸一到 (start, end)。
    """
    ps = s.get("page_start")
    pe = s.get("page_end")
    if isinstance(ps, int) and isinstance(pe, int):
        return (ps, pe) if ps <= pe else (pe, ps)
    sp = s.get("source_page")
    if isinstance(sp, int):
        return sp, sp
    pages = s.get("pages")
    if isinstance(pages, (list, tuple)) and len(pages) >= 1:
        try:
            start = int(pages[0])
            end = int(pages[-1])
            return (start, end) if start <= end else (end, start)
        except (TypeError, ValueError):
            pass
    return None, None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fail(db: Session, job: ResourceParseJob, reason: str) -> None:
    """ fail。"""
    job.status = ParseJobStatus.FAILED.value
    job.failure_reason = reason[:2000]
    job.finished_at = datetime.now(timezone.utc)
    db.flush()


def _extract_plain_text(markdown: str) -> str:
    """粗略去 markdown 語法以支援全文搜尋。"""
    import re

    s = markdown
    s = re.sub(r"!\[.*?\]\(.*?\)", "", s)          # images
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)  # links → text
    s = re.sub(r"[#>*_`]+", "", s)
    s = re.sub(r"\s+\n", "\n", s)
    return s.strip()
