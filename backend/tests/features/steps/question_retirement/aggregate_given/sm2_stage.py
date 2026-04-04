"""Given 該題 SM-2 排程目前為第 N 階段 — Aggregate Given"""

import uuid

from behave import given
from app.models.question_stat import QuestionStat
from app.models.question import Question


@given('該題 SM-2 排程目前為第 {stage:d} 階段')
def step_impl(context, stage):
    db = context.db_session
    question_id = uuid.UUID(context.memo["current_question_id"])

    # 取得 question 的 node_id（若無則建立一個）
    q = db.query(Question).filter_by(id=question_id).first()
    user_id = uuid.UUID(context.memo["current_user_id"])

    if q.node_id:
        # 更新 question_stats 以反映 SM-2 階段
        stat = db.query(QuestionStat).filter_by(
            user_id=user_id, node_id=q.node_id
        ).first()
        if not stat:
            stat = QuestionStat(
                user_id=user_id,
                node_id=q.node_id,
                success_count=stage,
                fail_count=0,
            )
            db.add(stat)
        else:
            stat.success_count = stage
        db.commit()

    context.memo["sm2_stage"] = stage
