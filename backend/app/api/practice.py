"""Practice API — V3 練習模式（即時更新知識圖譜進度）.

V3 有機生長：練習答題即時反映在進度上（回傳正確答案 + 詳解 + 更新 progress）。
"""

import uuid as uuid_mod

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.models.question import Question
from app.services.organic_progress import OrganicProgressEngine

router = APIRouter(prefix="/practice")


class PracticeSubmitRequest(BaseModel):
    question_id: str
    selected_answer: str


@router.post("/submit")
def submit_practice_answer(
    body: PracticeSubmitRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """提交練習作答 — 即時回傳答案 + 更新知識圖譜進度（V3 有機生長）。"""
    q = db.query(Question).filter(Question.id == uuid_mod.UUID(body.question_id)).first()
    if not q:
        raise HTTPException(status_code=404, detail={"message": "題目不存在"})

    is_correct = body.selected_answer == q.correct_answer

    # V3：即時更新 progress
    progress_update = None
    propagation = []
    if q.node_id:
        engine = OrganicProgressEngine(db)
        progress_update = engine.update_on_answer(
            user_id=user_id,
            node_id=str(q.node_id),
            is_correct=is_correct,
            weight=0.5,  # 練習權重 0.5（考試權重 1.0）
        )
        propagation = engine.propagate_upward(user_id, str(q.node_id))
        db.commit()

    return {
        "ok": True,
        "is_correct": is_correct,
        "correct_answer": q.correct_answer,
        "selected_answer": body.selected_answer,
        "explanation": q.explanation or "尚無詳解",
        "question_id": str(q.id),
        "mode": "practice",
        "state_updated": True,
        "progress": progress_update,
        "propagation": propagation,
    }
