"""Then 查詢結果不應包含 company_b 學生的 answers."""

from behave import then


@then('查詢結果不應包含 {slug} 學生的 answers')
def step_impl(context, slug):
    """驗證查詢結果不包含指定租戶的 answers。"""
    import uuid
    answers = context.query_result
    other_tenant_id = context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}")

    if other_tenant_id:
        uid = uuid.UUID(str(other_tenant_id))
        other_answers = [a for a in answers if a.tenant_id == uid]
        assert len(other_answers) == 0, \
            f"不應包含租戶 {slug} 的 answers，但找到 {len(other_answers)} 筆"
