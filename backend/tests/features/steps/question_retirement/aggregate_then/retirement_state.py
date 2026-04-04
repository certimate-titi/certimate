"""Then 退場狀態驗證 — Aggregate Then"""

import uuid

from behave import then
from app.models.question import Question


@then('這 {count:d} 題 AI 題的 retired_at 應被設定為當前時間')
def step_bulk_retired(context, count):
    db = context.db_session
    question_ids = context.memo.get("ai_question_ids", [])

    retired_count = 0
    for qid in question_ids:
        q = db.query(Question).filter_by(id=uuid.UUID(qid)).first()
        if q and q.retired_at is not None:
            retired_count += 1

    assert retired_count == count, \
        f"預期 {count} 題被退場，實際 {retired_count} 題"


@then('retention_reason 應為 "{reason}"')
def step_retention_reason(context, reason):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    if not question_id:
        question_ids = context.memo.get("ai_question_ids", [])
        question_id = question_ids[0] if question_ids else None

    assert question_id, "找不到題目 ID"
    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is not None, f"題目 {question_id} 不存在"
    assert q.retention_reason == reason, \
        f"retention_reason 預期 '{reason}'，實際 '{q.retention_reason}'"


@then('該題的 retired_at 應被設定為當前時間')
def step_single_retired(context):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is not None, f"題目 {question_id} 不存在"
    assert q.retired_at is not None, \
        f"題目 {question_id} retired_at 應不為 NULL"


@then('該題不應被退場')
def step_not_retired(context):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is not None, f"題目 {question_id} 不存在"
    assert q.retired_at is None, \
        f"題目 {question_id} retired_at 應為 NULL，實際 '{q.retired_at}'"


@then('retention_reason 應更新為 "{reason}"')
def step_retention_updated(context, reason):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is not None, f"題目 {question_id} 不存在"
    assert q.retention_reason == reason, \
        f"retention_reason 預期 '{reason}'，實際 '{q.retention_reason}'"


@then('該題的 retired_at 應被立即設定')
def step_immediate_retire(context):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is not None, f"題目 {question_id} 不存在"
    assert q.retired_at is not None, \
        f"題目 {question_id} retired_at 應不為 NULL"


@then('quality_flag 應更新為 "{flag}"')
def step_quality_updated(context, flag):
    db = context.db_session
    question_id = context.memo.get("current_question_id")
    assert question_id, "找不到題目 ID"

    q = db.query(Question).filter_by(id=uuid.UUID(question_id)).first()
    assert q is not None, f"題目 {question_id} 不存在"
    assert q.quality_flag == flag, \
        f"quality_flag 預期 '{flag}'，實際 '{q.quality_flag}'"


@then('該節點下的 AI 題 retired_at 應被設定為當前時間')
def step_node_retired(context):
    db = context.db_session
    node_id = uuid.UUID(context.memo["current_node_id"])

    questions = db.query(Question).filter_by(
        node_id=node_id, source_type="ai_generated"
    ).all()

    for q in questions:
        assert q.retired_at is not None, \
            f"節點下 AI 題 {q.id} retired_at 應不為 NULL"


@then('該科目下所有 AI 生成題目應被軟刪除')
def step_subject_retired(context):
    db = context.db_session
    question_ids = context.memo.get("ai_question_ids", [])

    for qid in question_ids:
        q = db.query(Question).filter_by(id=uuid.UUID(qid)).first()
        assert q is not None, f"題目 {qid} 不存在"
        assert q.retired_at is not None, \
            f"AI 題 {qid} retired_at 應不為 NULL"
