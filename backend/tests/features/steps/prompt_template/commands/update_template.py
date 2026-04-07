"""When: 更新 Prompt 模板 / 停用模板。"""

from behave import when


def _parse_table_to_dict(table):
    data = {}
    for row in table:
        key = row["欄位"]
        val = row["值"]
        data[key] = val
    return data


@when('使用者 "{email}" 更新 Prompt 模板 "{template_id}"：')
def step_impl(context, email, template_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    data = _parse_table_to_dict(context.table)

    if "temperature" in data:
        data["temperature"] = float(data["temperature"])
    if "max_tokens" in data and data["max_tokens"]:
        data["max_tokens"] = int(data["max_tokens"])

    response = context.api_client.patch(
        f"/api/v1/admin/prompt-templates/{template_id}",
        json=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 更新 Prompt 模板 "{template_id}" 的 system_prompt 為 "{value}"')
def step_impl(context, email, template_id, value):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.patch(
        f"/api/v1/admin/prompt-templates/{template_id}",
        json={"system_prompt": value},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 停用 Prompt 模板 "{template_id}"')
def step_impl(context, email, template_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.delete(
        f"/api/v1/admin/prompt-templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
