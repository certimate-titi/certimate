"""Then 題目標記複查狀態 — Aggregate Then"""

import uuid

from behave import then

from app.models.answer import Answer


@then('題目 {question_id:d} 的標記複查狀態應為 "{status}"')
def step_impl(context, question_id, status):
    db = context.db_session
    db.expire_all()
    question_uuid = uuid.UUID(int=question_id)

    saved = db.query(Answer).filter_by(
        question_id=question_uuid,
    ).first()

    assert saved is not None, \
        f"找不到題目 {question_id} 的作答記錄"

    expected = status in ("已標記", "true", "True", "1")
    assert saved.marked_for_review == expected, \
        f"預期標記複查為 {expected}，實際為 {saved.marked_for_review}"
