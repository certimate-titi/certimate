"""When: 查詢單一 Prompt 模板詳情。"""

from behave import when


@when('使用者 "{email}" 查詢 Prompt 模板 "{template_id}" 詳情')
def step_impl(context, email, template_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/admin/prompt-templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
