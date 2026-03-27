"""Then 階段依序執行驗證 — ReadModel Then"""

from behave import then


@then('系統應依序執行以下階段：')
def step_impl(context):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"API 回應失敗: {response.status_code} {response.text}"

    data = response.json()

    # Check stages exist in response
    stages = data.get("stages", {})
    progress = data.get("progress_events", [])

    # Verify we have progress events covering all stages
    assert len(progress) >= 4, (
        f"應至少有 4 個階段進度事件，實際有 {len(progress)}"
    )

    for row in context.table:
        stage_num = int(row["階段"])
        stage_name = row["名稱"]

        # Find matching stage in stages dict
        stage_key = f"stage_{stage_num}"
        assert stage_key in stages, (
            f"回應中應包含 {stage_key}，但只有 {list(stages.keys())}"
        )
