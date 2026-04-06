"""Then 錯題明細回應驗證 — ReadModel Then"""

from behave import then


@then('回應應包含 {count:d} 筆錯題紀錄')
def step_impl_count(context, count):
    response = context.last_response
    data = response.json()
    wrong_answers = data.get("wrong_answers", [])
    assert len(wrong_answers) == count, \
        f"期望 {count} 筆錯題, 實際 {len(wrong_answers)}"


@then('每筆錯題明細應包含：')
def step_impl_fields(context):
    response = context.last_response
    data = response.json()
    wrong_answers = data.get("wrong_answers", [])

    expected_fields = set()
    for row in context.table:
        expected_fields.add(row["欄位"])

    assert len(wrong_answers) > 0, "沒有錯題紀錄"

    for i, wa in enumerate(wrong_answers):
        for field in expected_fields:
            assert field in wa, \
                f"第 {i + 1} 筆錯題缺少欄位 '{field}', 有: {list(wa.keys())}"
