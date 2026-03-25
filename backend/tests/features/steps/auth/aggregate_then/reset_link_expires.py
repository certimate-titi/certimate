from behave import then


@then('重設連結應在 {hours:d} 小時後失效')
def step_impl(context, hours):
    response = context.last_response
    data = response.json()
    # 驗證回應中包含重設連結的過期時間資訊
    expires_hours = data.get("expires_in_hours") or data.get("expire_hours")
    assert expires_hours is not None, \
        f"回應中未包含重設連結過期時間資訊: {data}"
    assert int(expires_hours) == hours, \
        f"重設連結過期時間應為 {hours} 小時，實際為 {expires_hours}"
