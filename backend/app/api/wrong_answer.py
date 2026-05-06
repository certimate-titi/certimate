"""Wrong Answer API — 錯題複習與 AI 教練。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_db_with_tenant, get_current_user_id
from app.services.wrong_answer_service import WrongAnswerService
from app.services.ai_coach_service import AICoachService

router = APIRouter(prefix="/wrong-answers")


class CoachChatRequest(BaseModel):
    message: str


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


class PickRequest(BaseModel):
    """錯題考試挑題請求。"""
    subject_id: str | None = None
    question_count: int = 20  # 用戶選的題數，受 plan_limit 限制


class MarkMasteredRequest(BaseModel):
    """手動標記錯題已掌握。"""
    question_id: str


@router.post("/exam/pick")
def pick_wrong_answer_exam(
    body: PickRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """智能挑錯題考試（4 階段時程感知 + 多桶配額）。"""
    import uuid as _uuid
    from app.services.wrong_answer_picker import WrongAnswerPicker
    try:
        uid = _uuid.UUID(user_id)
        sid = _uuid.UUID(body.subject_id) if body.subject_id else None
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail={"message": "ID 格式錯誤"})
    picker = WrongAnswerPicker(db)
    result = picker.pick(user_id=uid, subject_id=sid, target_count=max(1, body.question_count))
    return result


@router.post("/questions/{question_id}/mark-mastered")
def mark_question_mastered(
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """手動標記題目為已掌握（從錯題本與錯題考試移除）。"""
    import uuid as _uuid
    from datetime import datetime, timezone
    from app.models.user_question_override import UserQuestionOverride
    from app.models.answer import Answer
    try:
        uid = _uuid.UUID(user_id)
        qid = _uuid.UUID(question_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail={"message": "ID 格式錯誤"})
    # 必須先有 answer 紀錄才能標記
    has_answer = db.query(Answer).filter_by(user_id=uid, question_id=qid).first()
    if not has_answer:
        raise HTTPException(status_code=403, detail={"message": "尚未對此題作答，無法標記"})
    existing = db.query(UserQuestionOverride).filter_by(user_id=uid, question_id=qid).first()
    if existing:
        existing.is_mastered = True
        existing.marked_at = datetime.now(timezone.utc)
    else:
        db.add(UserQuestionOverride(
            user_id=uid, question_id=qid, is_mastered=True,
            marked_at=datetime.now(timezone.utc),
        ))
    db.commit()
    return {"ok": True, "question_id": question_id, "is_mastered": True}


@router.delete("/questions/{question_id}/mark-mastered")
def unmark_question_mastered(
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取消已掌握標記（重新出現於錯題本）。"""
    import uuid as _uuid
    from app.models.user_question_override import UserQuestionOverride
    try:
        uid = _uuid.UUID(user_id)
        qid = _uuid.UUID(question_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail={"message": "ID 格式錯誤"})
    db.query(UserQuestionOverride).filter_by(user_id=uid, question_id=qid).delete()
    db.commit()
    return {"ok": True, "question_id": question_id, "is_mastered": False}


@router.get("/due-count")
def get_due_wrong_answer_count(
    subject_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """回傳該複習的錯題數量（過複習日的桶）— 給 /schedule 提醒用。"""
    import uuid as _uuid
    from app.services.wrong_answer_picker import WrongAnswerPicker
    from datetime import datetime, timezone
    try:
        uid = _uuid.UUID(user_id)
        sid = _uuid.UUID(subject_id) if subject_id else None
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail={"message": "ID 格式錯誤"})
    picker = WrongAnswerPicker(db)
    today = datetime.now(timezone.utc).date()
    candidates = picker._collect_candidates(uid, sid, today)
    buckets = picker._classify_to_buckets(candidates, today)
    return {
        "due_count": len(buckets["overdue"]),
        "fresh_count": len(buckets["fresh"]),
        "weak_count": len(buckets["weak"]),
        "total_candidates": len(candidates),
    }


# ========== Advanced AI Coach (ULTRA only) ==========

@router.get("/advanced-coach")
def get_advanced_coach(
    subject_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """ULTRA 專屬進階 AI 教練 — 弱點分析 + 突破策略 + 衝刺計畫。"""
    service = AICoachService(db)
    result = service.get_advanced_analysis(user_id=user_id, subject_id=subject_id)
    return _handle_result(result)


@router.get("/advanced-coach/history")
def get_learning_history(
    days: int = 30,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """ULTRA 專屬 — 近 N 天學習歷史摘要。"""
    service = AICoachService(db)
    result = service.get_learning_history_summary(user_id=user_id, days=days)
    return _handle_result(result)


@router.get("")
def list_wrong_answers(
    subject_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """list wrong answers。

    此 endpoint 對應 `list_wrong_answers` 操作。

    Args:
        subject_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerService(db)
    result = service.list_by_subject(user_id=user_id, subject_id=subject_id)
    return _handle_result(result)


@router.get("/questions/{question_id}/coach")
def get_coach_info_no_exam(
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """取得 AI 教練資訊（前端不帶 exam_id 的路由）。"""
    service = WrongAnswerService(db)
    result = service.get_coach_info(
        exam_id=None, user_id=user_id, question_id=question_id
    )
    return _handle_result(result)


@router.post("/questions/{question_id}/coach")
def ai_coach_chat_no_exam(
    question_id: str,
    body: CoachChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """AI 教練聊天（前端不帶 exam_id 的路由）。"""
    service = WrongAnswerService(db)
    result = service.ai_coach_chat(
        exam_id=None, user_id=user_id,
        question_id=question_id, message=body.message
    )
    return _handle_result(result)


@router.get("/{exam_id}")
def get_wrong_answers_by_exam(
    exam_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """get wrong answers by exam。

    此 endpoint 對應 `get_wrong_answers_by_exam` 操作。

    Args:
        exam_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerService(db)
    result = service.get_wrong_answers_by_exam(exam_id=exam_id, user_id=user_id)
    return _handle_result(result)


@router.get("/{exam_id}/questions/{question_id}/analysis")
def get_question_analysis(
    exam_id: str,
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """get question analysis。

    此 endpoint 對應 `get_question_analysis` 操作。

    Args:
        exam_id: 參數。
        question_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerService(db)
    result = service.get_analysis(
        exam_id=exam_id, user_id=user_id, question_id=question_id
    )
    return _handle_result(result)


@router.get("/{exam_id}/questions/{question_id}/coach")
def get_coach_info(
    exam_id: str,
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """get coach info。

    此 endpoint 對應 `get_coach_info` 操作。

    Args:
        exam_id: 參數。
        question_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerService(db)
    result = service.get_coach_info(
        exam_id=exam_id, user_id=user_id, question_id=question_id
    )
    return _handle_result(result)


@router.post("/{exam_id}/questions/{question_id}/coach")
def ai_coach_chat(
    exam_id: str,
    question_id: str,
    body: CoachChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),  # RLS: answers table
):
    """ai coach chat。

    此 endpoint 對應 `ai_coach_chat` 操作。

    Args:
        exam_id: 參數。
        question_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = WrongAnswerService(db)
    result = service.ai_coach_chat(
        exam_id=exam_id, user_id=user_id,
        question_id=question_id, message=body.message
    )
    return _handle_result(result)
