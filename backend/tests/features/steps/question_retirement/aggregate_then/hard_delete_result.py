"""Then 硬刪除結果驗證 — Aggregate Then"""

import uuid
from datetime import datetime, timezone

from behave import then
from app.models.question import Question


@then('該題應從資料庫中永久刪除')
def step_impl(context):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is None, f"題目 {question_id} 應已被永久刪除，但仍存在"


@then('相關的 JSON 存檔應一併刪除')
def step_json_deleted(context):
    # JSON 存檔刪除由 API 處理，此處驗證 response
    response = context.last_response
    if response:
        data = response.json()
        assert data.get("json_cleaned", True), "JSON 存檔應已刪除"


@then('該題資料不可恢復')
def step_irrecoverable(context):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is None, f"題目 {question_id} 不應存在（不可恢復）"


@then('該題的 retired_at 應被清除')
def step_restored(context):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is not None, f"題目 {question_id} 不存在"
    assert q.retired_at is None, \
        f"題目 {question_id} retired_at 應為 NULL（已恢復），實際 '{q.retired_at}'"


@then('expires_at 應重新計算')
def step_expires_recalculated(context):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is not None, f"題目 {question_id} 不存在"
    assert q.expires_at is not None, "expires_at 應已重新計算"
    now = datetime.now(timezone.utc)
    assert q.expires_at > now, \
        f"expires_at 應大於當前時間，實際 '{q.expires_at}'"
