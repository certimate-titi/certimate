"""Given 該題 SM-2 五階段已全部通過 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.question_stat import QuestionStat
from app.models.question import Question


@given('該題 SM-2 五階段已全部通過，完成日為 {days:d} 天前')
def step_impl(context, days):
    db = context.db_session
    question_id = uuid.UUID(context.memo["current_question_id"])
    user_id = uuid.UUID(context.memo["current_user_id"])
    completed_at = datetime.now(timezone.utc) - timedelta(days=days)

    q = db.query(Question).filter_by(id=question_id).first()
    if q.node_id:
        stat = db.query(QuestionStat).filter_by(
            user_id=user_id, node_id=q.node_id
        ).first()
        if not stat:
            stat = QuestionStat(
                user_id=user_id,
                node_id=q.node_id,
                success_count=5,
                fail_count=0,
            )
            db.add(stat)
            db.flush()
        else:
            stat.success_count = 5
        stat.updated_at = completed_at
        db.commit()

    context.memo["sm2_stage"] = 5
    context.memo["sm2_completed_at"] = completed_at
