"""Refresh Quiz API — 記憶喚醒迷你測驗 (P2.4).

衰退的知識節點可透過 Refresh Quiz 恢復有效進度。
"""

import uuid as uuid_mod
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.models.node_mastery import NodeMastery
from app.models.question import Question
from app.services.sm2_engine import SM2Engine, TopicState

router = APIRouter(prefix="/topics")


class RefreshQuizSubmit(BaseModel):
    answers: list[dict]  # [{"question_id": str, "selected_answer": str}]


@router.post("/{topic_id}/refresh-quiz")
def generate_refresh_quiz(
    topic_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """生成記憶喚醒迷你測驗（1-3 題）。"""
    uid = uuid_mod.UUID(user_id)
    nid = uuid_mod.UUID(topic_id)

    # 從題庫抽取 1-3 題（優先考古題）
    questions = (
        db.query(Question)
        .filter(Question.node_id == nid)
        .order_by(Question.id)
        .limit(3)
        .all()
    )

    if not questions:
        # Fallback: 從同一 exam 的題目中找
        questions = (
            db.query(Question)
            .filter(Question.historical_exam_id.isnot(None))
            .limit(3)
            .all()
        )

    if not questions:
        raise HTTPException(status_code=404, detail={"message": "無可用題目"})

    return {
        "topic_id": topic_id,
        "questions": [
            {
                "id": str(q.id),
                "content": q.content,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d,
            }
            for q in questions
        ],
    }


@router.post("/{topic_id}/refresh-quiz/submit")
def submit_refresh_quiz(
    topic_id: str,
    body: RefreshQuizSubmit,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """提交 Refresh Quiz 結果，更新記憶狀態。"""
    uid = uuid_mod.UUID(user_id)
    nid = uuid_mod.UUID(topic_id)
    now = datetime.now(timezone.utc)

    # 判斷是否全部答對
    all_correct = True
    for ans in body.answers:
        q = db.query(Question).filter(Question.id == uuid_mod.UUID(ans["question_id"])).first()
        if q and q.correct_answer != ans.get("selected_answer"):
            all_correct = False
            break

    # 載入現有 mastery
    mastery = db.query(NodeMastery).filter(
        NodeMastery.user_id == uid, NodeMastery.node_id == nid
    ).first()

    if not mastery:
        raise HTTPException(status_code=404, detail={"message": "找不到節點掌握度"})

    # SM-2 Refresh Quiz 結算
    engine = SM2Engine()
    old_state = TopicState(
        base_mastery=float(mastery.base_mastery or 0),
        ease_factor=float(mastery.ease_factor or 2.5),
        last_tested_at=mastery.last_tested_at,
        next_review_at=mastery.next_review_at,
        status=mastery.status or "UNSEEN",
    )

    new_state = engine.process_refresh_quiz(old_state, all_correct, now)

    # 寫回 DB
    mastery.base_mastery = new_state.base_mastery
    mastery.ease_factor = new_state.ease_factor
    mastery.last_tested_at = new_state.last_tested_at
    mastery.next_review_at = new_state.next_review_at
    mastery.status = new_state.status
    mastery.mastery_rate = round(new_state.base_mastery * 100, 2)
    mastery.color = {"MASTERED": "green", "PENDING": "yellow", "CRITICAL": "red"}.get(new_state.status, "gray")

    db.commit()

    effective = engine.calculate_effective_progress(new_state, now)

    return {
        "ok": True,
        "all_correct": all_correct,
        "base_mastery": new_state.base_mastery,
        "effective_progress": effective,
        "status": new_state.status,
        "next_review_at": new_state.next_review_at.isoformat() if new_state.next_review_at else None,
        "message": "記憶喚醒成功！" if all_correct else "部分答錯，已縮短複習間隔",
    }
