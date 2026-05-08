"""Resource LLM Parse API router — EPIC-035 (TASK-035-04 API 子任務).

Endpoints:
  POST   /resources/{id}/parse                          觸發解析（回 job）
  GET    /resources/{id}/parse-status                   查詢進度
  GET    /resources/{id}/parsed                         取 parsed_markdown + scaffolds
  GET    /resources/{id}/question-candidates            T1/T2/T3 分桶
  POST   /resources/{id}/question-candidates/approve    批次核可進 questions
  POST   /questions/{id}/concept-note                   記錄自述
  POST   /questions/{id}/blind-answer                   盲作答送出
  POST   /questions/{id}/inference-judgment             同意自己/AI/都不對
  POST   /resource-scaffolds/{id}/response              思考題作答
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id, get_db
from app.models.question import Question
from app.models.question_candidate import (
    QuestionCandidate,
    QuestionCandidateDecision,
)
from app.models.resource import Resource
from app.models.resource_parse_job import ResourceParseJob
from app.models.resource_scaffold import ResourceScaffold
from app.models.user import User
from app.services.resource_parse_quota_service import (
    QuotaExceededError,
    check_and_consume,
)
from app.services.resource_parse_service import create_parse_job, run_parse_job


router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ParseJobResponse(BaseModel):
    job_id: UUID
    resource_id: UUID
    status: str


class ParseStatusResponse(BaseModel):
    job_id: UUID
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    failure_reason: str | None
    detected_content_type: str | None
    critical_pages: list[int]


class ParsedResourceResponse(BaseModel):
    resource_id: UUID
    parsed_markdown: str | None
    detected_content_type: str | None
    trust_level: int | None
    scaffolds: list[dict[str, Any]]


class CandidateItem(BaseModel):
    id: UUID
    question_text: str
    options: list[str]
    ai_inferred_answer: str | None
    confidence: float | None
    source_page: int | None
    tier: str


class CandidateListResponse(BaseModel):
    t1_count: int = Field(..., description="T1 已直接入庫，回傳 count 供 UI 顯示")
    t2: list[CandidateItem]
    t3: list[CandidateItem]


class ApproveCandidatesRequest(BaseModel):
    candidate_ids: list[UUID]
    approve: bool = True  # False = reject


class ConceptNoteRequest(BaseModel):
    note: str = Field(..., min_length=1, max_length=2000)


class BlindAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=10)


class InferenceJudgmentRequest(BaseModel):
    judgment: str = Field(..., pattern=r"^(agree_self|agree_ai|neither)$")


class ScaffoldResponseRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _as_uuid(v: UUID | str) -> UUID:
    return v if isinstance(v, UUID) else UUID(str(v))


def _get_user_or_404(db: Session, user_id: UUID | str) -> User:
    user = db.get(User, _as_uuid(user_id))
    if not user:
        raise HTTPException(status_code=404, detail={"message": "user not found"})
    return user


def _require_paid_plan(db: Session, user_id: UUID | str) -> None:
    """學習鷹架 / 教材 Tab 是 PRO 以上專屬功能（TASK-04）。"""
    user = _get_user_or_404(db, user_id)
    plan = user.subscription_plan
    plan_val = plan.value if hasattr(plan, "value") else plan
    if plan_val in (None, "FREE"):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "學習教材為 PRO 以上方案功能",
                "paywall": True,
                "upgrade": {
                    "target_plan": "PRO_199",
                    "message": "升級 PRO 解鎖 AI 學習教材與延伸思考",
                },
            },
        )


def _get_resource_owned(db: Session, resource_id: UUID, user_id: UUID | str) -> Resource:
    uid = _as_uuid(user_id)
    res = db.get(Resource, resource_id)
    if not res:
        raise HTTPException(status_code=404, detail={"message": "resource not found"})
    if res.user_id != uid:
        raise HTTPException(status_code=403, detail={"message": "forbidden"})
    return res


def _get_question_owned(db: Session, question_id: UUID, user_id: UUID | str) -> Question:
    uid = _as_uuid(user_id)
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(status_code=404, detail={"message": "question not found"})
    if q.owner_user_id and q.owner_user_id != uid:
        raise HTTPException(status_code=403, detail={"message": "forbidden"})
    return q


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

# NOTE: POST /resources/{id}/parse endpoint removed (2026-05-08).
# Reparse 功能下架原因：prompt 由 super_admin 統一管理，相同 prompt × 相同 PDF
# 重跑只是燒 LLM 成本，無產品價值。配額觸發點移到 /upload-file。


@router.get(
    "/resources/{resource_id}/parse-status", response_model=ParseStatusResponse
)
def get_parse_status(
    resource_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> ParseStatusResponse:
    """get parse status。

    此 endpoint 對應 `get_parse_status` 操作。

    Args:
        resource_id: 參數。
        current_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    _get_resource_owned(db, resource_id, current_user_id)
    job = db.execute(
        select(ResourceParseJob)
        .where(ResourceParseJob.resource_id == resource_id)
        .order_by(ResourceParseJob.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail={"message": "no parse job"})
    return ParseStatusResponse(
        job_id=job.id,
        status=job.status,
        started_at=job.started_at,
        finished_at=job.finished_at,
        failure_reason=job.failure_reason,
        detected_content_type=job.detected_content_type,
        critical_pages=list(job.critical_pages or []),
    )


@router.get("/resources/{resource_id}/markdown")
def get_markdown(
    resource_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> dict:
    """取得 multimodal Pro 解析後的完整 markdown（含圖片引用）。

    所有 plan（含 FREE）皆可讀；scaffolds / 題目等付費功能走 /parsed。
    對應「原文閱讀」UI — 點擊資源即可看到含圖排版 markdown。

    回傳同時帶 parse_status 給前端判斷是否仍在解析中（避免空字串 = 失敗的誤判）。
    """
    res = _get_resource_owned(db, resource_id, current_user_id)
    job = db.execute(
        select(ResourceParseJob)
        .where(ResourceParseJob.resource_id == resource_id)
        .order_by(ResourceParseJob.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return {
        "resource_id": str(res.id),
        "filename": res.name,
        "markdown": res.parsed_markdown or "",
        "status": (res.status.value if hasattr(res.status, "value") else res.status),
        "parse_status": (job.status if job else None),
        "parse_started_at": (job.started_at.isoformat() if job and job.started_at else None),
        "parse_failure_reason": (job.failure_reason if job else None),
    }


@router.get("/resources/{resource_id}/parsed", response_model=ParsedResourceResponse)
def get_parsed(
    resource_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> ParsedResourceResponse:
    """get parsed。

    此 endpoint 對應 `get_parsed` 操作。

    Args:
        resource_id: 參數。
        current_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    _require_paid_plan(db, current_user_id)
    res = _get_resource_owned(db, resource_id, current_user_id)
    scaffolds_rows = db.execute(
        select(ResourceScaffold)
        .where(ResourceScaffold.resource_id == resource_id)
        .order_by(ResourceScaffold.created_at)
    ).scalars().all()
    return ParsedResourceResponse(
        resource_id=res.id,
        parsed_markdown=res.parsed_markdown,
        detected_content_type=res.detected_content_type,
        trust_level=res.trust_level,
        scaffolds=[
            {
                "id": str(s.id),
                "chapter_heading": s.chapter_heading,
                "type": s.type,
                "content": s.content,
                "user_response": s.user_response,
            }
            for s in scaffolds_rows
        ],
    )


@router.get(
    "/resources/{resource_id}/question-candidates",
    response_model=CandidateListResponse,
)
def list_candidates(
    resource_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> CandidateListResponse:
    """list candidates。

    此 endpoint 對應 `list_candidates` 操作。

    Args:
        resource_id: 參數。
        current_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    _get_resource_owned(db, resource_id, current_user_id)

    t1_count = db.execute(
        select(Question)
        .where(Question.source_resource_id == resource_id)
    ).scalars().all()
    rows = db.execute(
        select(QuestionCandidate)
        .where(QuestionCandidate.resource_id == resource_id)
        .where(QuestionCandidate.decision == QuestionCandidateDecision.PENDING.value)
    ).scalars().all()

    def _to_item(r: QuestionCandidate) -> CandidateItem:
        return CandidateItem(
            id=r.id,
            question_text=r.question_text,
            options=list(r.options or []),
            ai_inferred_answer=r.ai_inferred_answer,
            confidence=float(r.confidence) if r.confidence is not None else None,
            source_page=r.source_page,
            tier=r.tier,
        )

    return CandidateListResponse(
        t1_count=len(t1_count),
        t2=[_to_item(r) for r in rows if r.tier == "T2"],
        t3=[_to_item(r) for r in rows if r.tier == "T3"],
    )


@router.post("/resources/{resource_id}/question-candidates/approve")
def approve_candidates(
    resource_id: UUID,
    body: ApproveCandidatesRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> dict[str, int]:
    """approve candidates。

    此 endpoint 對應 `approve_candidates` 操作。

    Args:
        resource_id: 參數。
        body: 參數。
        current_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    resource = _get_resource_owned(db, resource_id, current_user_id)

    approved = 0
    rejected = 0
    for cid in body.candidate_ids:
        cand = db.get(QuestionCandidate, cid)
        if not cand or cand.resource_id != resource_id:
            continue
        cand.decided_at = datetime.now(timezone.utc)
        if body.approve:
            cand.decision = QuestionCandidateDecision.APPROVED.value
            # 進 questions 表（個人題庫）
            needs_answer = not cand.ai_inferred_answer
            q = Question(
                content=cand.question_text,
                option_a=cand.options[0] if len(cand.options) > 0 else None,
                option_b=cand.options[1] if len(cand.options) > 1 else None,
                option_c=cand.options[2] if len(cand.options) > 2 else None,
                option_d=cand.options[3] if len(cand.options) > 3 else None,
                correct_answer=cand.ai_inferred_answer or "?",
                source_resource_id=resource.id,
                owner_user_id=resource.user_id,
                source_type="user_upload",
                tenant_id=resource.tenant_id,
                answer_source="user_confirmed",
                confidence=cand.confidence,
                needs_answer=needs_answer,
                never_for_scoring=needs_answer
                    or (cand.confidence is not None and float(cand.confidence) < 0.9),
                question_number=cand.source_page or 0,
            )
            db.add(q)
            approved += 1
        else:
            cand.decision = QuestionCandidateDecision.REJECTED.value
            rejected += 1

    db.commit()
    return {"approved": approved, "rejected": rejected}


@router.post("/questions/{question_id}/concept-note")
def set_concept_note(
    question_id: UUID,
    body: ConceptNoteRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> dict[str, str]:
    """set concept note。

    此 endpoint 對應 `set_concept_note` 操作。

    Args:
        question_id: 參數。
        body: 參數。
        current_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    q = _get_question_owned(db, question_id, current_user_id)
    q.user_concept_note = body.note.strip()
    q.user_concept_note_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "ok"}


@router.post("/questions/{question_id}/blind-answer")
def submit_blind_answer(
    question_id: UUID,
    body: BlindAnswerRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """submit blind answer。

    此 endpoint 對應 `submit_blind_answer` 操作。

    Args:
        question_id: 參數。
        body: 參數。
        current_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    q = _get_question_owned(db, question_id, current_user_id)
    if not q.needs_answer:
        raise HTTPException(
            status_code=400,
            detail={"message": "此題不屬於 needs_answer；請走一般作答流程"},
        )
    # 揭曉 AI 推論（從 correct_answer + explanation 取）
    return {
        "user_answer": body.answer,
        "ai_inferred_answer": q.correct_answer,
        "ai_confidence": float(q.confidence) if q.confidence is not None else None,
        "ai_reasoning": q.explanation or "",
        "never_for_scoring": q.never_for_scoring,
        "next_step": "submit_judgment",
    }


@router.post("/questions/{question_id}/inference-judgment")
def set_inference_judgment(
    question_id: UUID,
    body: InferenceJudgmentRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> dict[str, str]:
    """set inference judgment。

    此 endpoint 對應 `set_inference_judgment` 操作。

    Args:
        question_id: 參數。
        body: 參數。
        current_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    q = _get_question_owned(db, question_id, current_user_id)
    # 僅更新 explanation 尾巴記錄判定（avoid new table for MVP）
    existing = q.explanation or ""
    tag = f"\n\n[user_judgment:{body.judgment}@{datetime.now(timezone.utc).isoformat()}]"
    q.explanation = (existing + tag)[:8000]
    db.commit()
    return {"status": "ok", "judgment": body.judgment}


@router.post("/resource-scaffolds/{scaffold_id}/response")
def set_scaffold_response(
    scaffold_id: UUID,
    body: ScaffoldResponseRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> dict[str, str]:
    """set scaffold response。

    此 endpoint 對應 `set_scaffold_response` 操作。

    Args:
        scaffold_id: 參數。
        body: 參數。
        current_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    s = db.get(ResourceScaffold, scaffold_id)
    if not s:
        raise HTTPException(status_code=404, detail={"message": "scaffold not found"})
    # 確認 scaffold 隸屬於該用戶的 resource
    res = db.get(Resource, s.resource_id)
    if not res or res.user_id != _as_uuid(current_user_id):
        raise HTTPException(status_code=403, detail={"message": "forbidden"})
    s.user_response = body.content.strip()
    s.responded_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "ok"}
