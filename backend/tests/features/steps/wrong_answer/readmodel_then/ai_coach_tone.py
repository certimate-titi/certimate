"""Then AI 教練回覆語氣驗證 — ReadModel Then"""

from behave import then


@then('AI 教練回覆語氣應帶有鼓勵性（非冷冰冰的條列式）')
def step_impl(context):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "")
    assert reply, f"AI 教練回覆為空，回應：{data}"
    # 鼓勵性語氣驗證：回覆中應包含鼓勵性詞彙
    encouragement_keywords = ["加油", "不錯", "很好", "繼續", "👍", "😊", "別擔心", "沒關係", "理解"]
    has_encouragement = any(kw in reply for kw in encouragement_keywords)
    assert has_encouragement, \
        f"AI 教練回覆缺乏鼓勵性語氣，回覆：{reply[:200]}"
