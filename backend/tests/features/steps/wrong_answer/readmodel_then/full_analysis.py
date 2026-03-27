"""Then 回應應包含完整的 Markdown 格式深度解析（非空白） — ReadModel Then"""

from behave import then


@then('回應應包含完整的 Markdown 格式深度解析（非空白）')
def step_impl(context):
    response = context.last_response
    data = response.json()

    deep_analysis = data.get("deep_analysis", "")
    assert deep_analysis and len(deep_analysis.strip()) > 0, \
        f"預期深度解析非空白，實際 '{deep_analysis}'"
    assert data.get("deep_analysis_locked") is not True, \
        "PRO 以上用戶的深度解析不應為鎖定狀態"
