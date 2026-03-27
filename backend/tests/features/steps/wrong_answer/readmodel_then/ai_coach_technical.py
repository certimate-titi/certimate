"""Then AI 教練回覆技術術語驗證 — ReadModel Then"""

from behave import then


@then('AI 教練回覆應直接使用技術術語（如 CloudWatch Alarm、Target Tracking Policy）')
def step_impl(context):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "")
    assert reply, f"AI 教練回覆為空，回應：{data}"
    # 驗證包含技術術語
    technical_keywords = ["CloudWatch", "Target Tracking", "API", "Policy", "Scaling"]
    has_technical = any(kw in reply for kw in technical_keywords)
    assert has_technical, \
        f"AI 教練回覆缺乏技術術語，回覆：{reply[:200]}"


@then('AI 教練回覆可引用 API 參數或 CLI 指令作為補充')
def step_impl_cli(context):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "")
    assert reply, f"AI 教練回覆為空，回應：{data}"
    # 寬鬆驗證：回覆非空即可（CLI 引用為選擇性）
