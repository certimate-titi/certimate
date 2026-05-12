"""Then assertions — Feature 46 enqueue failure BDD."""

import uuid

from behave import then

from app.models.resource import Resource


@then('拋出 EnqueueFailedError')
def step_assert_enqueue_failed_raised(context):
    exc = context.memo.get("enqueue_raised")
    assert exc is not None, (
        f"預期 EnqueueFailedError 被拋出，實際無例外"
        f"（other={context.memo.get('enqueue_raised_other')!r}）"
    )


@then('錯誤訊息含 "{snippet}"')
def step_assert_error_msg_contains(context, snippet):
    exc = context.memo.get("enqueue_raised")
    if exc is None:
        # 嘗試從 endpoint_error 抓
        msg = context.memo.get("endpoint_error", "")
    else:
        msg = str(exc)
    assert snippet in msg, (
        f"預期錯誤訊息含 {snippet!r}，實際: {msg!r}"
    )


@then('該 resource status 變為 {status}')
def step_assert_resource_status_changed(context, status):
    db = context.db_session
    rid = uuid.UUID(context.memo["last_resource_id"])
    res = db.query(Resource).filter_by(id=rid).first()
    assert res is not None, "找不到資源"
    actual = res.status.value if hasattr(res.status, "value") else str(res.status)
    assert actual == status, f"預期 status={status}，實際={actual}"


@then('該 resource error_message 含 "{snippet}"')
def step_assert_resource_error_contains(context, snippet):
    db = context.db_session
    rid = uuid.UUID(context.memo["last_resource_id"])
    res = db.query(Resource).filter_by(id=rid).first()
    assert res is not None, "找不到資源"
    msg = res.error_message or ""
    assert snippet in msg, (
        f"預期 error_message 含 {snippet!r}，實際: {msg!r}"
    )


@then('該 parse_job status 變為 {status}')
def step_assert_parse_job_status_changed(context, status):
    from app.models.resource_parse_job import ResourceParseJob
    db = context.db_session
    db.expire_all()  # 強制重新讀 DB
    jid = uuid.UUID(context.memo["last_parse_job_id"])
    job = db.query(ResourceParseJob).filter_by(id=jid).first()
    assert job is not None, "找不到 parse_job"
    actual = job.status.value if hasattr(job.status, "value") else str(job.status)
    assert actual == status, f"預期 parse_job.status={status}，實際={actual}"


@then('該 parse_job failure_reason 為 "{reason}"')
def step_assert_parse_job_failure_reason(context, reason):
    from app.models.resource_parse_job import ResourceParseJob
    db = context.db_session
    db.expire_all()
    jid = uuid.UUID(context.memo["last_parse_job_id"])
    job = db.query(ResourceParseJob).filter_by(id=jid).first()
    assert job is not None, "找不到 parse_job"
    assert job.failure_reason == reason, (
        f"預期 failure_reason={reason!r}，實際={job.failure_reason!r}"
    )


@then('對應 resource status 變為 {status}')
def step_assert_resource_status_via_parse_job(context, status):
    db = context.db_session
    db.expire_all()
    rid = uuid.UUID(context.memo["last_resource_id"])
    res = db.query(Resource).filter_by(id=rid).first()
    assert res is not None, "找不到資源"
    actual = res.status.value if hasattr(res.status, "value") else str(res.status)
    assert actual == status, f"預期 resource.status={status}，實際={actual}"


@then('該 parse_job status 仍為 {status}')
def step_assert_parse_job_status_unchanged(context, status):
    """冪等性與不應修改的斷言 — 使用同一個函式。"""
    step_assert_parse_job_status_changed(context, status)
