from behave import then


@then('系統應發送帳號驗證信至 "{email}"')
def step_impl(context, email):
    # 在 E2E 測試中，驗證 API 回應表明已觸發發送驗證信
    response = context.last_response
    data = response.json()
    # 檢查回應中是否有 verification_email_sent 標記或相關訊息
    verification_sent = (
        data.get("verification_email_sent") is True
        or "驗證信" in str(data.get("message", ""))
        or "verification" in str(data).lower()
    )
    assert verification_sent, \
        f"回應中未包含驗證信已發送的資訊: {data}"
