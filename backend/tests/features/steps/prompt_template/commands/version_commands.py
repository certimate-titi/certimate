"""When: 查詢版本歷史 / 回滾模板。"""

from behave import when


@when('使用者 "{email}" 查詢 Prompt 模板 "{template_id}" 的版本歷史')
def step_impl(context, email, template_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/admin/prompt-templates/{template_id}/versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 將 Prompt 模板 "{template_id}" 回滾至版本 {version:d}')
def step_impl(context, email, template_id, version):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.post(
        f"/api/v1/admin/prompt-templates/{template_id}/rollback",
        json={"version": version},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
