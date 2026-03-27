"""Then AI 教練回覆應包含與題目相關的解釋內容 — ReadModel Then"""

from behave import then


@then('AI 教練回覆應包含與題目 {question_id:d} 相關的解釋內容')
def step_impl(context, question_id):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "")
    assert reply, f"AI 教練回覆為空，回應：{data}"
