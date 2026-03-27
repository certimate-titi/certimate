"""Then 系統應依序執行以下階段 — ReadModel Then"""

from behave import then


@then('系統應依序執行以下階段：')
def step_impl(context):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"預期成功，實際 {response.status_code}: {response.text}"

    data = response.json()
    stages = data.get("stages", {})

    for row in context.table:
        stage_num = int(row["階段"])
        stage_name = row["名稱"]
        stage_key = f"stage_{stage_num}"

        assert stage_key in stages, \
            f"回應中找不到 {stage_key}，有 {list(stages.keys())}"

        stage_data = stages[stage_key]
        assert stage_data is not None, f"階段 {stage_num} ({stage_name}) 的輸出為空"
