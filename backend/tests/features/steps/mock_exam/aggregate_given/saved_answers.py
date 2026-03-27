"""Given 測驗 N 包含以下已暫存作答 — Aggregate Given"""

import uuid

from behave import given

from app.models.answer import Answer


@given('測驗 {exam_id:d} 包含以下已暫存作答：')
def step_impl(context, exam_id):
    db = context.db_session
    exam_uuid = uuid.UUID(int=exam_id)

    # Get user_id for this exam from context
    from app.models.exam import Exam
    exam = db.query(Exam).filter_by(id=exam_uuid).first()
    user_id = exam.user_id

    for row in context.table:
        q_id_int = int(row["題目 ID"])
        selected = row["選擇答案"]
        marked_raw = row["已標記複查"]
        marked = marked_raw in ("是", "true", "True", "1")

        answer = Answer(
            exam_id=exam_uuid,
            question_id=uuid.UUID(int=q_id_int),
            user_id=user_id,
            selected_answer=selected,
            marked_for_review=marked,
        )
        db.add(answer)

    db.commit()
