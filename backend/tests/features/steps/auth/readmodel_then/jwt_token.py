from behave import then


@then('回應應包含有效的 JWT 存取憑證')
def step_impl(context):
    response = context.last_response
    data = response.json()
    token = data.get("access_token") or data.get("token")
    assert token is not None and len(token) > 0, \
        f"回應中找不到有效的 JWT token: {data}"

    # 驗證 token 格式（JWT 為三段 base64 以 . 分隔）
    parts = token.split(".")
    assert len(parts) == 3, \
        f"JWT token 格式不正確（應為三段），實際為 {len(parts)} 段"
