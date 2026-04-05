"""When 使用者嘗試存取管理 API — Command"""

from behave import when


@when('使用者 "{email}" 嘗試存取管理 API "{method}" "{api_path}"')
def step_impl(context, email, method, api_path):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    if method.upper() == "GET":
        response = context.api_client.get(api_path, headers=headers)
    elif method.upper() == "POST":
        response = context.api_client.post(api_path, json={}, headers=headers)
    else:
        response = context.api_client.get(api_path, headers=headers)
    context.last_response = response
