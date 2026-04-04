"""Then 題目 source_type 驗證 — Aggregate Then"""

import uuid
from datetime import timedelta

from behave import then
from app.models.question import Question


@then('所有生成的題目 source_type 應為 "{source_type}"')
def step_impl(context, source_type):
    db = context.db_session
    question_ids = context.memo.get("ai_question_ids", [])

    for qid in question_ids:
        q = db.query(Question).filter_by(id=uuid.UUID(qid)).first()
        assert q is not None, f"題目 {qid} 不存在"
        assert q.source_type == source_type, \
            f"題目 {qid} source_type 預期 '{source_type}'，實際 '{q.source_type}'"


@then('所有生成的題目 quality_flag 應為 "{flag}"')
def step_quality_flag(context, flag):
    db = context.db_session
    question_ids = context.memo.get("ai_question_ids", [])

    for qid in question_ids:
        q = db.query(Question).filter_by(id=uuid.UUID(qid)).first()
        assert q is not None, f"題目 {qid} 不存在"
        assert q.quality_flag == flag, \
            f"題目 {qid} quality_flag 預期 '{flag}'，實際 '{q.quality_flag}'"


@then('所有生成的題目 expires_at 應為生成時間加 {days:d} 天')
def step_expires_at(context, days):
    db = context.db_session
    question_ids = context.memo.get("ai_question_ids", [])

    for qid in question_ids:
        q = db.query(Question).filter_by(id=uuid.UUID(qid)).first()
        assert q is not None, f"題目 {qid} 不存在"
        assert q.expires_at is not None, f"題目 {qid} expires_at 不應為 NULL"


@then('所有匯入的題目 source_type 應為 "{source_type}"')
def step_imported_source(context, source_type):
    db = context.db_session
    # 查詢最近匯入的題目（source_type=historical）
    questions = db.query(Question).filter_by(source_type=source_type).all()
    assert len(questions) > 0, f"找不到 source_type='{source_type}' 的題目"


@then('所有匯入的題目 expires_at 應為 NULL')
def step_imported_no_expiry(context):
    db = context.db_session
    questions = db.query(Question).filter_by(source_type="historical").all()
    for q in questions:
        assert q.expires_at is None, \
            f"考古題 {q.id} expires_at 應為 NULL，實際 '{q.expires_at}'"
