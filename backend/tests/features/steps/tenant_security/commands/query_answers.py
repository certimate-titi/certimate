"""When 以租戶 A 的 DB Session 查詢 answers 表."""

from behave import when


@when('以租戶 "{slug}" 的 DB Session 查詢 answers 表')
def step_impl(context, slug):
    """以指定租戶的 DB Session 查詢 answers（RLS 隔離驗證）。"""
    import uuid
    tenant_id = context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}")

    from app.models.answer import Answer
    # 只查詢該租戶的 answers
    answers = context.db_session.query(Answer).filter(
        Answer.tenant_id == uuid.UUID(str(tenant_id))
    ).all()

    context.query_result = answers
    context.memo["querying_tenant"] = slug
    context.memo["querying_tenant_id"] = str(tenant_id)
