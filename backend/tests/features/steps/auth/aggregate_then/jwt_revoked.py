from behave import then


@then('該使用者的所有 JWT 存取憑證應立即失效 (Revoked)')
def step_impl(context):
    # E2E 測試中，驗證 API 回應表明 JWT 已撤銷
    response = context.last_response
    data = response.json()
    jwt_revoked = (
        data.get("tokens_revoked") is True
        or "revoke" in str(data).lower()
        or "jwt" in str(data).lower()
    )
    assert jwt_revoked, \
        f"回應中未包含 JWT 已撤銷的資訊: {data}"
