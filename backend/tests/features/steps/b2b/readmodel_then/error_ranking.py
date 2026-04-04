"""Then 回應應包含最多 10 筆題目 / 每筆題目包含欄位 — ReadModel Then"""

from behave import then


@then('回應應包含最多 {max_count:d} 筆題目')
def step_impl(context, max_count):
    response = context.last_response
    data = response.json()
    questions = data.get("questions", [])
    assert len(questions) <= max_count, \
        f"預期最多 {max_count} 筆，實際 {len(questions)} 筆"


@then('每筆題目應包含：')
def step_impl_fields(context):
    response = context.last_response
    data = response.json()
    questions = data.get("questions", [])
    # Even if empty, schema should be correct
    required_fields = [row["欄位"] for row in context.table]

    if len(questions) > 0:
        for q in questions:
            for field in required_fields:
                assert field in q, \
                    f"題目中找不到欄位 '{field}'，實際: {list(q.keys())}"
