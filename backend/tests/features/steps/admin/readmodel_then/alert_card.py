"""Then 營運儀表板應顯示紅色警報卡片 — Read Model Then"""

from behave import then


@then('營運儀表板應顯示紅色警報卡片，內容為「{expected_content}」')
def step_impl(context, expected_content):
    response = context.last_response
    data = response.json()

    alerts = data.get("alerts", [])
    assert len(alerts) > 0, f"回應中沒有警報卡片：{data}"

    matched = False
    for alert in alerts:
        content = alert.get("content", alert.get("message", ""))
        level = alert.get("level", alert.get("severity", ""))
        if expected_content in content and level in ("red", "critical", "error"):
            matched = True
            break

    assert matched, \
        f"找不到紅色警報卡片，內容為「{expected_content}」，實際 alerts：{alerts}"
