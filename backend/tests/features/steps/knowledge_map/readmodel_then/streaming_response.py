"""Then 回應應以串流方式輸出 AI 教練回覆 — ReadModel Then"""

from behave import then


@then('回應應以串流方式輸出 AI 教練回覆')
def step_impl(context):
    response = context.last_response
    data = response.json()

    # 驗證回應中包含串流標記或 AI 回覆內容
    assert data.get("streaming") is True or data.get("reply"), (
        "回應應包含串流標記 (streaming=true) 或 AI 回覆內容 (reply)"
    )
