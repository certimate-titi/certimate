"""When Prompt 模板管理操作 — Command"""

from behave import when


@when('使用者 "{email}" 嘗試修改階段 {stage_id:d} 的 Prompt 模板')
def step_user_try_modify(context, email, stage_id):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    token = context.jwt_helper.generate_token(context.ids[email])

    response = context.api_client.put(
        f"/api/v1/exams/prompt-templates/{stage_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "test modification"},
    )
    context.last_response = response


@when('管理員修改階段 {stage_id:d} Prompt 模板，新增指示「{instruction}」')
def step_admin_modify_template(context, stage_id, instruction):
    token = context.memo.get("admin_token")
    assert token, "管理員尚未登入"

    response = context.api_client.put(
        f"/api/v1/exams/prompt-templates/{stage_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": instruction},
    )
    context.last_response = response


@when('管理員查看階段 {stage_id:d} Prompt 模板的歷史版本')
def step_admin_view_history(context, stage_id):
    token = context.memo.get("admin_token")
    assert token, "管理員尚未登入"

    response = context.api_client.get(
        f"/api/v1/exams/prompt-templates/{stage_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
