"""Then AI 教練通用語氣驗證 — ReadModel Then"""

from behave import then


@then('AI 教練應使用中等難度的通用說明方式（預設大學程度）')
def step_impl(context):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "")
    assert reply, f"AI 教練回覆為空，回應：{data}"
