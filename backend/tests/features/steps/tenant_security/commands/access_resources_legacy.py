"""When 使用舊格式 Token 呼叫 GET /api/v1/resources."""

from behave import when


@when("使用該 Token 呼叫 GET /api/v1/resources")
def step_impl(context):
    """使用舊格式 JWT（不含 tenant_id）呼叫 resources API。"""
    token = context.memo.get("legacy_token") or context.memo.get("current_token")
    response = context.api_client.get(
        "/api/v1/resources",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
