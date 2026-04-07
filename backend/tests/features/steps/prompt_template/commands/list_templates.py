"""When: 查詢 Prompt 模板列表。"""

from behave import when


@when('使用者 "{email}" 查詢 Prompt 模板列表')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        "/api/v1/admin/prompt-templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢 Prompt 模板列表，分類為 "{category}"')
def step_impl(context, email, category):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/admin/prompt-templates?category={category}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
