"""Then 暫存作答應為 — Aggregate Then"""

import uuid

from behave import then

from app.models.answer import Answer


@then('測驗 {exam_id:d} 中題目 {question_id:d} 的暫存作答應為 "{answer}"')
def step_impl(context, exam_id, question_id, answer):
    db = context.db_session
    db.expire_all()
    exam_uuid = uuid.UUID(int=exam_id)
    question_uuid = uuid.UUID(int=question_id)

    saved = db.query(Answer).filter_by(
        exam_id=exam_uuid,
        question_id=question_uuid,
    ).first()

    assert saved is not None, \
        f"找不到測驗 {exam_id} 題目 {question_id} 的作答記錄"
    assert saved.selected_answer == answer, \
        f"預期作答為 '{answer}'，實際為 '{saved.selected_answer}'"
