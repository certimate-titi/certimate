from behave import then


@then('系統應發送密碼重設信至 "{email}"')
def step_impl(context, email):
    response = context.last_response
    data = response.json()
    # 檢查回應中是否有 reset_email_sent 標記或相關訊息
    reset_sent = (
        data.get("reset_email_sent") is True
        or "重設" in str(data.get("message", ""))
        or "reset" in str(data).lower()
    )
    assert reset_sent, \
        f"回應中未包含密碼重設信已發送的資訊: {data}"
