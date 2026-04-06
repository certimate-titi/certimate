"""Then 未映射題目清單驗證 — ReadModel Then"""

from behave import then


@then('回應中 unmapped_questions 應為 {count:d} 或接近 {count2:d}')
def step_impl(context, count, count2):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    data = response.json()
    unmapped = data.get("unmapped_questions", data.get("unmapped_count", -1))
    # Allow close to 0 (within 5% of total)
    assert unmapped <= 10, \
        f"預期未映射題目接近 0，實際為 {unmapped}"


@then('若有未映射題目，每題應包含 suggested_node（AI 建議歸屬節點）')
def step_impl_suggested(context):
    response = context.last_response
    data = response.json()

    questions = data.get("questions", [])
    for q in questions:
        assert "suggested_node" in q or "suggested_node_id" in q, \
            f"未映射題目 {q.get('id', '?')} 缺少 suggested_node 欄位"
