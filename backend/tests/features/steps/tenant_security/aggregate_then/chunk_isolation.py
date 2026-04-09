"""Then 查詢結果應只包含 company_a 的 {count} 個 chunks."""

from behave import then


@then('查詢結果應只包含 {slug} 的 {count:d} 個 chunks')
def step_impl(context, slug, count):
    """驗證查詢結果只包含指定租戶的 chunks。"""
    chunks = context.query_result
    assert chunks is not None, "查詢結果為 None"
    assert len(chunks) == count, \
        f"期望 {count} 個 chunks，實際得到 {len(chunks)} 個"

    tenant_id = context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}")
    for chunk in chunks:
        assert str(chunk.tenant_id) == str(tenant_id), \
            f"chunk {chunk.id} 屬於錯誤的租戶：期望 {tenant_id}，實際 {chunk.tenant_id}"


@then('不應看到 {slug} 的 {count:d} 個 chunks')
def step_impl_not(context, slug, count):
    """驗證查詢結果不包含指定租戶的 chunks。"""
    import uuid
    chunks = context.query_result
    other_tenant_id = context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}")

    if other_tenant_id:
        uid = uuid.UUID(str(other_tenant_id))
        other_chunks = [c for c in chunks if c.tenant_id == uid]
        assert len(other_chunks) == 0, \
            f"不應看到租戶 {slug} 的資料，但找到 {len(other_chunks)} 個 chunks"
