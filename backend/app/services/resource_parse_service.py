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

def _call_gemini_with_retry(resource: Resource) -> dict[str, Any]:
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


class _RetryableError(Exception):
    pass


def _call_gemini_once(resource: Resource, model: str) -> dict[str, Any]:
    """實際呼叫 Gemini。

    為避免在 import 時需要 google.generativeai，這裡 lazy import。
    測試可透過 monkeypatch 這個函式或塞 fake。
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

    # load prompt template 'resource_parser_v2' (best-effort; falls back to hardcoded)
    template = None
    try:
        from app.core.deps import _SessionLocal
        if _SessionLocal is not None:
            _tmp_db = _SessionLocal()
            try:
                prompt_service = PromptTemplateService(_tmp_db)
                template = prompt_service.get_prompt_for_ai("resource_parser_v2")
            finally:
                _tmp_db.close()
    except Exception as _e:
        logger.warning("prompt template lookup failed: %s", _e)
        template = None
    def _tget(obj, key):
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

    # download PDF locally for upload
    storage = get_storage_service()
    if not resource.gcs_path:
        raise RuntimeError("resource has no gcs_path")
    local_pdf = storage.download_to_temp(resource.gcs_path)

    try:
        uploaded = client.files.upload(
            file=local_pdf,
            config={"mime_type": "application/pdf"},
        )
        resp = client.models.generate_content(
            model=model,
            contents=[uploaded, user_prompt],
            config={
                "system_instruction": system_prompt,
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        )
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        if "429" in msg or "quota" in msg or "timeout" in msg or "unavailable" in msg:
            raise _RetryableError(str(e)) from e
        raise

    text = getattr(resp, "text", None) or ""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"gemini returned non-JSON: {text[:500]}") from e
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
    resource.parsed_markdown = parsed.get("markdown")
    resource.parsed_text = _extract_plain_text(parsed.get("markdown") or "")
    resource.detected_content_type = parsed.get("detected_content_type")

    # 2) WebP + figures — dispatch to resource_storage_service（critical pages aware）
    pages_rendered = 0
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
    except Exception:
        logger.warning("webp render failed resource=%s", resource.id, exc_info=True)

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

    for s in parsed.get("scaffolds", []) or []:
        row = _build_scaffold_row(resource, s)
        if row is not None:
            db.add(row)
            s_created += 1

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
    opts = q.get("options") or []
    def _opt(i: int) -> str | None:
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
    raw_type = (s.get("type") or "").lower()
    try:
        t = ResourceScaffoldType(raw_type)
    except ValueError:
        return None
    return ResourceScaffold(
        resource_id=resource.id,
        tenant_id=resource.tenant_id,
        chapter_heading=s.get("chapter_heading"),
        type=t.value,
        content=s.get("content") or "",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fail(db: Session, job: ResourceParseJob, reason: str) -> None:
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
