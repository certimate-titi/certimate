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


@router.get("/nodes/{node_id}/questions")
def get_node_questions(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """查詢知識節點下的練習題列表。"""
    nid = uuid_mod.UUID(node_id)

    questions = (
        db.query(Question)
        .filter(Question.node_id == nid)
        .order_by(Question.question_number)
        .all()
    )

    return {
        "node_id": node_id,
        "questions": [
            {
                "id": str(q.id),
                "content": q.content,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d,
                "figure_urls": list(q.figure_urls or []),
                "figure_description": q.figure_description,
                "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else q.difficulty,
                "type": q.type.value if hasattr(q.type, "value") else q.type,
                "needs_answer": bool(getattr(q, "needs_answer", False)),
                "answer_source": getattr(q, "answer_source", None),
                "confidence": float(q.confidence) if getattr(q, "confidence", None) is not None else None,
                "never_for_scoring": bool(getattr(q, "never_for_scoring", False)),
            }
            for q in questions
        ],
        "total": len(questions),
    }


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

    # V3：即時更新 progress（never_for_scoring 題目排除於統計/進度更新）
    progress_update = None
    propagation = []
    if q.node_id and not q.never_for_scoring:
        engine = OrganicProgressEngine(db)
        progress_update = engine.update_on_answer(
            user_id=user_id,
            node_id=str(q.node_id),
            is_correct=is_correct,
            weight=0.5,  # 練習權重 0.5（考試權重 1.0）
        )
        propagation = engine.propagate_upward(user_id, str(q.node_id))

        # Daily quest hook — count distinct practiced nodes
        try:
            from app.services.daily_quest_service import DailyQuestService
            DailyQuestService(db).record_node_practiced(user_id, str(q.node_id))
        except Exception:
            pass

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
        "answer_source": getattr(q, "answer_source", None),
        "confidence": float(q.confidence) if getattr(q, "confidence", None) is not None else None,
        "never_for_scoring": bool(getattr(q, "never_for_scoring", False)),
    }
