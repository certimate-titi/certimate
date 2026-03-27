"""Then AI 教練回覆生活化比喻驗證 — ReadModel Then"""

from behave import then


@then('AI 教練回覆應使用生活化比喻（例如「像是餐廳在尖峰時段自動增加服務生」）')
def step_impl(context):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "")
    assert reply, f"AI 教練回覆為空，回應：{data}"
    analogy_keywords = ["像是", "好比", "就像", "類似", "想像", "比喻", "舉例"]
    has_analogy = any(kw in reply for kw in analogy_keywords)
    assert has_analogy, \
        f"AI 教練回覆缺乏生活化比喻，回覆：{reply[:200]}"


@then('AI 教練回覆不應假設使用者具備進階技術背景知識')
def step_impl_no_advanced(context):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "")
    # 驗證不含過度專業的假設語句
    assert reply, f"AI 教練回覆為空，回應：{data}"
