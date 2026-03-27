"""Then AI 教練回覆引用歷史錯題 — ReadModel Then"""

from behave import then


@then('AI 教練回覆應提及使用者在 {node_keyword} 相關題目的歷史錯誤模式')
def step_impl(context, node_keyword):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "")
    assert reply, f"AI 教練回覆為空，回應：{data}"
    assert node_keyword in reply or "歷史" in reply or "之前" in reply or "過去" in reply, \
        f"AI 教練回覆未提及 '{node_keyword}' 相關的歷史錯誤，回覆：{reply[:200]}"
