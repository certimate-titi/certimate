"""When steps for Prompt template management — Command"""

from behave import when


@when('使用者 "{email}" 嘗試修改階段 {stage_id:d} 的 Prompt 模板')
def step_impl(context, email, stage_id):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.put(
        f"/api/v1/exams/prompt-templates/{stage_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "嘗試修改的內容"},
    )
    context.last_response = response


@when('管理員修改階段 {stage_id:d} Prompt 模板，新增指示「{instruction}」')
def step_impl(context, stage_id, instruction):
    token = context.memo.get("admin_token")
    if not token:
        raise KeyError("管理員未登入")

    response = context.api_client.put(
        f"/api/v1/exams/prompt-templates/{stage_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": f"更新的 Prompt 模板：{instruction}"},
    )
    context.last_response = response
    context.memo["updated_stage_id"] = stage_id


@when('管理員查看階段 {stage_id:d} Prompt 模板的歷史版本')
def step_impl(context, stage_id):
    token = context.memo.get("admin_token")
    if not token:
        raise KeyError("管理員未登入")

    response = context.api_client.get(
        f"/api/v1/exams/prompt-templates/{stage_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
