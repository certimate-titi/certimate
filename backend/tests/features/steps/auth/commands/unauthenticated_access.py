"""When 未登入使用者嘗試存取 API — Command"""

from behave import when


@when('未登入使用者嘗試存取 "{method}" "{api_path}"')
def step_impl(context, method, api_path):
    """Send request without JWT token."""
    if method.upper() == "GET":
        response = context.api_client.get(api_path)
    elif method.upper() == "POST":
        response = context.api_client.post(api_path, json={})
    else:
        response = context.api_client.get(api_path)
    context.last_response = response
