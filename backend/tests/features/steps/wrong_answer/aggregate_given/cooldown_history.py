"""Given 使用者在過去 10 分鐘內已提出 N 次超出範圍的問題 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.ai_cooldown import AiCooldown


@given('使用者 "{email}" 在過去 10 分鐘內已提出 {count:d} 次超出範圍的問題')
def step_impl(context, email, count):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    now = datetime.now(timezone.utc)
    for i in range(count):
        record = AiCooldown(
            user_id=user_uuid,
            reason="out_of_scope",
            cooldown_until=now,
        )
        db.add(record)

    db.commit()

    # Store exam/question context for the command step
    from app.models.exam import Exam
    from app.models.question import Question
    exam = db.query(Exam).filter_by(user_id=user_uuid).first()
    if exam:
        question = db.query(Question).filter_by(exam_id=exam.id).first()
        if question:
            context.memo["cooldown_exam_id"] = str(exam.id)
            context.memo["cooldown_question_id"] = str(question.id)
