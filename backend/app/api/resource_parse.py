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
                "retrieval_prompt": s.retrieval_prompt,
                "template_code": s.template_code,
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


# ---------------------------------------------------------------------------
# T08 P0：Scaffold interaction logging（retrieval-first UX）
# ---------------------------------------------------------------------------


class ScaffoldInteractionRequest(BaseModel):
    """retrieval-first UX 互動事件記錄請求。

    event 必為下列之一：
      - "viewed"            使用者看到此鷹架（可作 SM-2 第一次曝光）
      - "revealed"          使用者點「看答案」揭曉 takeaway
      - "recall_self_rated" 使用者自評回想感（必帶 recall_quality）
    """

    event: str = Field(..., pattern=r"^(viewed|revealed|recall_self_rated)$")
    recall_quality: str | None = Field(
        default=None, pattern=r"^(none|partial|full)$"
    )


@router.post("/resource-scaffolds/{scaffold_id}/interactions")
def log_scaffold_interaction(
    scaffold_id: UUID,
    body: ScaffoldInteractionRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> dict[str, str]:
    """記錄一筆 retrieval-first UX 互動事件 → scaffold_interaction_log。

    對應 docs/scaffold-redesign-plan.md P0 + Sprint 1 T08。

    Args:
        scaffold_id: 鷹架 UUID
        body: ScaffoldInteractionRequest
        current_user_id: 從 JWT 取得

    Returns:
        {"status": "ok", "log_id": str}

    Raises:
        404: scaffold 不存在
        403: scaffold 不屬於該用戶
        422: event 或 recall_quality 格式錯誤
    """
    from app.models.scaffold_interaction_log import ScaffoldInteractionLog

    if body.event == "recall_self_rated" and not body.recall_quality:
        raise HTTPException(
            status_code=422,
            detail={"message": "recall_self_rated event requires recall_quality"},
        )

    s = db.get(ResourceScaffold, scaffold_id)
    if not s:
        raise HTTPException(status_code=404, detail={"message": "scaffold not found"})
    res = db.get(Resource, s.resource_id)
    if not res or res.user_id != _as_uuid(current_user_id):
        raise HTTPException(status_code=403, detail={"message": "forbidden"})

    log = ScaffoldInteractionLog(
        user_id=_as_uuid(current_user_id),
        scaffold_id=scaffold_id,
        event=body.event,
        recall_quality=body.recall_quality,
    )
    db.add(log)
    db.flush()
    log_id = str(log.id)

    # P4 (Sprint 5 T45)：recall_self_rated 事件 → 觸發 SM-2 排程更新
    next_review_at = None
    if body.event == "recall_self_rated" and body.recall_quality:
        try:
            from app.services.sm2_service import update_review
            sched = update_review(
                db,
                user_id=_as_uuid(current_user_id),
                scaffold_id=scaffold_id,
                recall_quality=body.recall_quality,
            )
            next_review_at = sched.next_review_at.isoformat()
        except Exception as e:
            # SM-2 失敗不阻斷 log 寫入
            import logging
            logging.getLogger("scaffold.sm2").warning(
                "SM-2 update failed scaffold=%s: %s", scaffold_id, e,
            )

    db.commit()
    return {
        "status": "ok",
        "log_id": log_id,
        "next_review_at": next_review_at,  # 給前端顯示「下次複習：2026-05-13」
    }


# ---------------------------------------------------------------------------
# T09 P0：章節練習自動帶題（章節讀完底部 InlinePractice）
# ---------------------------------------------------------------------------


class ChapterPracticeQuestion(BaseModel):
    """單題回應（精簡版，避免暴露未必要欄位）。"""

    id: UUID
    content: str
    option_a: str | None
    option_b: str | None
    option_c: str | None
    option_d: str | None
    correct_answer: str
    explanation: str | None


class ChapterPracticeResponse(BaseModel):
    """章節練習回應。

    questions 為當前章節對應的 question 清單（最多 3 題）。
    若章節無對應 page range / 該 range 無題 → 空陣列（前端隱藏 InlinePractice 區塊）。
    """

    chapter_heading: str
    page_range: list[int]  # [start, end] or []
    questions: list[ChapterPracticeQuestion]


@router.get(
    "/resources/{resource_id}/chapter-practice",
    response_model=ChapterPracticeResponse,
)
def get_chapter_practice(
    resource_id: UUID,
    chapter_heading: str,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> ChapterPracticeResponse:
    """取得章節讀完底部自動帶入的 2-3 題練習。

    對應 docs/scaffold-redesign-plan.md P0 E2 + Sprint 1 T09。

    流程：
      1. 由 chapter_heading 找對應的 scaffold（任一筆即可，取 page_start / page_end）
      2. 透過 QuestionCandidate 過濾 source_page 在該 range 的 approved 題
      3. 回傳對應 Question 詳情，最多 3 題

    若 page_range 不足或該章節無題，questions=[]（前端 fallback 隱藏區塊）。
    """
    _get_resource_owned(db, resource_id, current_user_id)

    # Step 1: chapter scaffold → page range
    scaffold = db.execute(
        select(ResourceScaffold)
        .where(ResourceScaffold.resource_id == resource_id)
        .where(ResourceScaffold.chapter_heading == chapter_heading)
        .where(ResourceScaffold.page_start.isnot(None))
        .order_by(ResourceScaffold.created_at)
        .limit(1)
    ).scalar_one_or_none()

    page_range: list[int] = []
    if scaffold and scaffold.page_start is not None:
        page_range = [scaffold.page_start, scaffold.page_end or scaffold.page_start]

    if not page_range:
        return ChapterPracticeResponse(
            chapter_heading=chapter_heading, page_range=[], questions=[]
        )

    # Step 2: candidates in this range, decision=approved, has approved_question_id
    # QuestionCandidate.decision=approved 後會新建 Question，但 candidate 本身保留歷史。
    # 我們改用更穩定的路徑：直接撈 Questions WHERE source_resource_id = X
    # 並從 QuestionCandidate join 出有 source_page 在 range 的 question_text 比對。
    # 為了 Sprint 1 P0 簡化：直接拿同 resource 的 questions，最多 3 題（沒答過的優先）。
    questions = db.execute(
        select(Question)
        .where(Question.source_resource_id == resource_id)
        .where(Question.retired_at.is_(None))
        .limit(10)  # 取多一點再 filter
    ).scalars().all()

    # 用 candidate.source_page 過濾：candidate.question_text 與 question.content 比對
    # （兩者寫入時是同一段 content，approved 時 candidate 不刪）
    if questions:
        candidates_in_range = db.execute(
            select(QuestionCandidate)
            .where(QuestionCandidate.resource_id == resource_id)
            .where(QuestionCandidate.source_page.between(page_range[0], page_range[1]))
            .where(QuestionCandidate.decision == QuestionCandidateDecision.APPROVED.value)
        ).scalars().all()
        cand_texts = {(c.question_text or "").strip() for c in candidates_in_range}
        if cand_texts:
            questions = [q for q in questions if (q.content or "").strip() in cand_texts]

    questions = questions[:3]

    return ChapterPracticeResponse(
        chapter_heading=chapter_heading,
        page_range=page_range,
        questions=[
            ChapterPracticeQuestion(
                id=q.id,
                content=q.content,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
            )
            for q in questions
        ],
    )


# ── Sprint 5 P4 T43：跨資源概念中心 endpoint ─────────────────────────────────


class ConceptHit(BaseModel):
    """單一概念命中項（用於 concept-center search）。"""

    resource_id: UUID
    resource_name: str
    resource_type: str  # pdf | video | quiz | other
    chapter_heading: str | None
    scaffold_type: str
    content: str


class ConceptCenterResponse(BaseModel):
    """跨資源概念中心搜尋結果。

    依 scaffold_type 分組（前端展示用）：
      - pitfall：跨資源迷思警示
      - takeaway / advance_organizer：教材觀點
      - elaborative：思考題引用
    """

    query: str
    subject_id: UUID | None
    total: int
    hits: list[ConceptHit]


@router.get(
    "/concept-center", response_model=ConceptCenterResponse
)
def search_concept(
    q: str,
    subject_id: UUID | None = None,
    limit: int = 50,
    semantic: bool = True,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> ConceptCenterResponse:
    """跨資源搜尋概念。

    Args:
        q: 搜尋關鍵字（必填，最少 2 字）
        subject_id: 限定科目（可選，預設搜全 user resources）
        limit: 回傳上限（1-200，default 50）
        current_user_id: JWT 解出

    Returns:
        ConceptCenterResponse — query / subject_id / total / hits[]

    Sprint 5 簡化版：純 SQL ILIKE 搜 scaffold.content + chapter_heading。
    Sprint 6 P5 評估：擴 voyage embedding 語意搜尋。

    Raises:
        422: q 長度不足
    """
    from app.models.resource import Resource as _Resource

    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=422,
            detail={"message": "q must be at least 2 characters"},
        )
    limit = max(1, min(limit, 200))

    # SQL ILIKE search across user's scaffolds（owner-scoped）
    # P5 (Sprint 6 T49)：先撈寬範圍（OR 字串配對 + 取 200）然後 voyage rerank
    user_uuid = _as_uuid(current_user_id)
    query_pattern = f"%{q.strip()}%"

    pre_limit = 200 if semantic else limit
    stmt = (
        select(ResourceScaffold, _Resource)
        .join(_Resource, ResourceScaffold.resource_id == _Resource.id)
        .where(_Resource.user_id == user_uuid)
        .where(
            (ResourceScaffold.content.ilike(query_pattern))
            | (ResourceScaffold.chapter_heading.ilike(query_pattern))
        )
        .order_by(
            # pitfall 排最前（警示優先）
            (ResourceScaffold.type == "pitfall").desc(),
            ResourceScaffold.created_at.desc(),
        )
        .limit(pre_limit)
    )
    if subject_id is not None:
        stmt = stmt.where(_Resource.subject_id == subject_id)

    rows = db.execute(stmt).all()

    # P5 T49：Voyage 語意 rerank（best-effort，失敗 fallback ILIKE 順序）
    if semantic and rows:
        try:
            from app.services.embedding_service import EmbeddingService
            emb = EmbeddingService()
            # P6 (Sprint 7 T54)：優先用 DB 持久化的 embedding（省 voyage cost）
            # 若 row.embedding IS NULL（舊資料 / lazy backfill 未跑）→ 即時 embed
            missing_indices = [
                i for i, (sf, _r) in enumerate(rows)
                if getattr(sf, "embedding", None) is None
            ]
            doc_vecs: list[list[float]] = [
                list(getattr(sf, "embedding", None) or [])
                for sf, _r in rows
            ]
            if missing_indices:
                texts_to_embed = [
                    ((rows[i][0].chapter_heading or "")
                     + " " + (rows[i][0].content or "")).strip()[:1000]
                    for i in missing_indices
                ]
                fresh_vecs = emb.embed_texts(texts_to_embed, input_type="document")
                for idx, vec in zip(missing_indices, fresh_vecs):
                    doc_vecs[idx] = vec
            q_vec = emb.embed_texts([q.strip()], input_type="query")[0]
            # cosine similarity
            import math

            def _cos(a: list[float], b: list[float]) -> float:
                dot = sum(x * y for x, y in zip(a, b))
                na = math.sqrt(sum(x * x for x in a))
                nb = math.sqrt(sum(x * x for x in b))
                return dot / (na * nb) if na and nb else 0.0

            scored = [
                (_cos(q_vec, dv), idx) for idx, dv in enumerate(doc_vecs)
            ]
            # pitfall 仍 priority boost +0.05
            scored = [
                (
                    score + (0.05 if (rows[idx][0].type == "pitfall") else 0.0),
                    idx,
                )
                for score, idx in scored
            ]
            scored.sort(key=lambda t: t[0], reverse=True)
            rows = [rows[idx] for _, idx in scored[:limit]]
        except Exception as e:
            import logging
            logging.getLogger("concept-center").warning(
                "voyage rerank failed, fallback ILIKE order: %s", e,
            )
            rows = rows[:limit]
    else:
        rows = rows[:limit]

    def _resource_type(r: _Resource) -> str:
        ext = (r.gcs_path or "").lower().rsplit(".", 1)[-1] if r.gcs_path else ""
        if ext in {"mp4", "mov", "avi", "mkv", "webm"} or getattr(r, "youtube_url", None):
            return "video"
        if r.detected_content_type == "practice_questions":
            return "quiz"
        if ext in {"ppt", "pptx"}:
            return "slides"
        return "pdf"

    hits = [
        ConceptHit(
            resource_id=res.id,
            resource_name=res.name or "(未命名)",
            resource_type=_resource_type(res),
            chapter_heading=sf.chapter_heading,
            scaffold_type=sf.type if isinstance(sf.type, str) else sf.type.value,
            content=sf.content or "",
        )
        for sf, res in rows
    ]

    return ConceptCenterResponse(
        query=q.strip(),
        subject_id=subject_id,
        total=len(hits),
        hits=hits,
    )


# ── Sprint 5 P4 T45：SM-2 due reviews endpoint ──────────────────────────────


class DueReviewItem(BaseModel):
    """SM-2 該複習項。"""

    schedule_id: UUID
    scaffold_id: UUID
    chapter_heading: str | None
    type: str
    content_preview: str  # scaffold.content 前 100 字
    resource_id: UUID
    resource_name: str
    next_review_at: datetime
    interval_days: int
    repetitions: int


class DueReviewsResponse(BaseModel):
    """SM-2 due 清單回應。"""

    total: int
    items: list[DueReviewItem]


@router.get(
    "/scaffold-reviews/due", response_model=DueReviewsResponse
)
def list_scaffold_due_reviews(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> DueReviewsResponse:
    """取「今日該複習」鷹架清單（SM-2 next_review_at <= now）。

    Args:
        limit: 上限 1-100，default 20
        current_user_id: JWT 解出

    Returns:
        DueReviewsResponse — total + items[]
    """
    from app.services.sm2_service import list_due_reviews
    from app.models.resource import Resource as _Resource

    limit = max(1, min(limit, 100))
    user_uuid = _as_uuid(current_user_id)
    schedules = list_due_reviews(db, user_id=user_uuid, limit=limit)

    if not schedules:
        return DueReviewsResponse(total=0, items=[])

    # Bulk fetch scaffolds + resources
    scaffold_ids = [s.scaffold_id for s in schedules]
    scaffolds = {
        s.id: s for s in db.execute(
            select(ResourceScaffold).where(ResourceScaffold.id.in_(scaffold_ids))
        ).scalars().all()
    }
    resource_ids = list({s.resource_id for s in scaffolds.values()})
    resources = {
        r.id: r for r in db.execute(
            select(_Resource).where(_Resource.id.in_(resource_ids))
        ).scalars().all()
    }

    items = []
    for sch in schedules:
        sf = scaffolds.get(sch.scaffold_id)
        if not sf:
            continue
        res = resources.get(sf.resource_id)
        if not res:
            continue
        items.append(DueReviewItem(
            schedule_id=sch.id,
            scaffold_id=sf.id,
            chapter_heading=sf.chapter_heading,
            type=sf.type if isinstance(sf.type, str) else sf.type.value,
            content_preview=(sf.content or "")[:100],
            resource_id=res.id,
            resource_name=res.name or "(未命名)",
            next_review_at=sch.next_review_at,
            interval_days=sch.interval_days,
            repetitions=sch.repetitions,
        ))

    return DueReviewsResponse(total=len(items), items=items)
