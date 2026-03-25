from behave import when


ACTION_ENDPOINT_MAP = {
    "刪除帳號": ("/api/v1/auth/delete-account", "DELETE"),
}


@when('使用者 "{email}" 執行 "{action}" 操作')
def step_impl(context, email, action):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    endpoint, method = ACTION_ENDPOINT_MAP.get(action, (None, None))
    assert endpoint is not None, f"未知的操作: '{action}'"

    if method == "DELETE":
        response = context.api_client.delete(endpoint, headers=headers)
    elif method == "POST":
        response = context.api_client.post(endpoint, headers=headers)
    else:
        response = context.api_client.post(endpoint, headers=headers)

    context.last_response = response
    context.memo["last_action_email"] = email
