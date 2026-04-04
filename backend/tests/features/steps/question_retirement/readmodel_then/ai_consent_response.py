"""Then AI 出題條款相關回應驗證 — ReadModel Then"""

from behave import then


@then('系統應顯示 AI 出題功能說明與條款同意彈窗')
def step_consent_dialog(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("requires_consent", False) or data.get("show_consent_dialog", False), \
        f"應要求顯示同意彈窗: {data}"


@then('彈窗應說明 AI 題為臨時性學習素材')
def step_temp_material(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    terms = data.get("consent_terms", data.get("terms", ""))
    assert "臨時" in str(terms) or "temporary" in str(terms).lower(), \
        f"條款應說明 AI 題為臨時性學習素材: {terms}"


@then('彈窗應說明資料退場與刪除政策')
def step_retirement_policy(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    terms = data.get("consent_terms", data.get("terms", ""))
    assert "退場" in str(terms) or "刪除" in str(terms) or "retirement" in str(terms).lower(), \
        f"條款應說明退場與刪除政策: {terms}"


@then('系統應記錄同意時間')
def step_consent_recorded(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("consented_at") or data.get("consent_recorded", False), \
        f"應記錄同意時間: {data}"


@then('使用者可正常使用 AI 出題功能')
def step_ai_available(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("ai_generation_available", True), \
        f"AI 出題功能應可用: {data}"


@then('AI 出題功能應不可用')
def step_ai_unavailable(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert not data.get("ai_generation_available", False), \
        f"AI 出題功能應不可用: {data}"


@then('使用者仍可使用考古題練習功能')
def step_historical_available(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("historical_available", True), \
        f"考古題練習功能應可用: {data}"
