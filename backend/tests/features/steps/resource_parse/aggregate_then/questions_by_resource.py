"""EPIC-035 aggregate Then — DB 驗證 approved questions."""

import uuid

from behave import then
from sqlalchemy import select

from app.models.question import Question


@then('DB 中 source_resource_id=該資源 的 questions 應有 {n:d} 筆')
def count_questions(context, n):
    rid = uuid.UUID(context.memo["last_resource_id"])
    rows = context.db_session.execute(
        select(Question).where(Question.source_resource_id == rid)
    ).scalars().all()
    assert len(rows) == n, f"預期 {n} 筆 questions，實際 {len(rows)}"
    context.memo["last_questions"] = rows


@then('該 {n:d} 筆 questions 的 owner_user_id 應等於 "{email}" 的 user_id')
def owner_matches(context, n, email):
    expected = uuid.UUID(context.ids[email])
    rows = context.memo["last_questions"]
    assert len(rows) == n
    for q in rows:
        assert q.owner_user_id == expected, \
            f"question {q.id} owner_user_id={q.owner_user_id}，期望 {expected}"
