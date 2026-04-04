"""Then 不應呼叫 AI 生成服務 — ReadModel Then"""

from behave import then


@then('不應呼叫 AI 生成服務')
def step_impl(context):
    response = context.last_response
    data = response.json()

    ai_generated = data.get("ai_generated_count", 0)
    assert ai_generated == 0, (
        f"不應呼叫 AI 生成服務，但有 {ai_generated} 題為 AI 生成"
    )
