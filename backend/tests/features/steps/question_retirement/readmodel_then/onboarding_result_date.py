"""Then Onboarding 放榜日期顯示驗證 — ReadModel Then"""

from behave import then


@then('已選科目列表應顯示考試日期與放榜日期')
def step_impl(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"

    data = response.json()
    # 驗證 response 包含 exam_date 和 result_date
    if isinstance(data, list):
        subjects = data
    else:
        subjects = data.get("subjects", data.get("selected_subjects", [data]))
    for s in subjects:
        assert "exam_date" in s, f"回應應包含 exam_date: {data}"
        assert "result_date" in s, f"回應應包含 result_date: {data}"
