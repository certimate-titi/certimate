"""Then 回應應標記深度解析區為鎖定狀態 — ReadModel Then"""

from behave import then


@then('回應應標記深度解析區為鎖定狀態')
def step_impl(context):
    response = context.last_response
    data = response.json()

    assert data.get("deep_analysis_locked") is True, \
        f"預期 deep_analysis_locked=True，實際 {data.get('deep_analysis_locked')}"
