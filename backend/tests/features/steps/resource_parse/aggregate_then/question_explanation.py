"""EPIC-035 M3 問題 explanation 欄位驗證。"""

import uuid

from behave import then

from app.models.question import Question


@then('DB 中該題 explanation 欄位應包含 "{text}"')
def step_explanation_contains(context, text):
    qid = uuid.UUID(context.memo["last_question_id"])
    q = context.db_session.get(Question, qid)
    assert q is not None, f"找不到題目 {qid}"
    explanation = q.explanation or ""
    assert text in explanation, \
        f"explanation 未包含 '{text}'，實際：{explanation!r}"
