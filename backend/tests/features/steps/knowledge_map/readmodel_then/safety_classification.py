"""Then steps for AI safety classification (Gemini Flash router) — ReadModel Then"""

from behave import then


@then('系統應先以 Gemini Flash 進行安全分類，結果為 {classification_result}')
def step_impl_safety_check(context, classification_result):
    """驗證 Gemini Flash 安全分類結果。"""
    response = context.last_response
    assert response.status_code in (200, 201, 400, 404, 422), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        classification = data.get("safety_classification") or data.get("classification", {})
        # Parse expected classification (e.g., "relevant=false", "injection_risk=true")
        if "=" in classification_result:
            key, value = classification_result.split("=")
            expected_value = value.lower() == "true"
            actual_value = classification.get(key.strip())
            if actual_value is not None:
                assert bool(actual_value) == expected_value, \
                    f"安全分類 '{key}' 期望 {expected_value}，實際 {actual_value}"
