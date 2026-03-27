"""Then AI 教練回覆應包含特定訊息 — ReadModel Then"""

from behave import then


@then('AI 教練回覆應包含「{message}」')
def step_impl(context, message):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "") or data.get("message", "")
    assert message in reply, \
        f"AI 教練回覆應包含「{message}」，實際回覆：{reply[:200]}"
