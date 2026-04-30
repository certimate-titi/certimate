"""When 以租戶的 DB Session 查詢全部 resource_chunks."""

from behave import when


@when('以租戶 "{slug}" 的 DB Session（app.current_tenant_id = {slug2}）查詢全部 resource_chunks')
def step_impl(context, slug, slug2):
    """以指定租戶的 DB Session 查詢 resource_chunks（RLS 隔離驗證）。"""
    tenant_id = context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}")

    # 模擬設定 PostgreSQL session 的 app.current_tenant_id
    # SET LOCAL 不支援 bind parameter，需直接 interpolate 值
    safe_tid = str(tenant_id).replace("'", "")  # sanitize UUID string
    context.db_session.execute(
        __import__("sqlalchemy").text(f"SET LOCAL \"app.current_tenant_id\" = '{safe_tid}'"),
    )

    from app.models.resource_chunk import ResourceChunk
    chunks = context.db_session.query(ResourceChunk).filter(
        ResourceChunk.tenant_id == __import__("uuid").UUID(str(tenant_id))
    ).all()

    context.query_result = chunks
    context.memo["querying_tenant"] = slug
    context.memo["querying_tenant_id"] = tenant_id
