"""When/Given resource hard-delete API 呼叫（GET delete-preview / DELETE）。"""

from behave import given, when


def _resolve_resource_id(context, alias):
    return context.ids.get(alias, alias)


@when('使用者 "{email}" 呼叫 GET /api/v1/resources/{res_alias}/delete-preview')
def step_get_preview(context, email, res_alias):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    rid = _resolve_resource_id(context, res_alias)
    response = context.api_client.get(
        f"/api/v1/resources/{rid}/delete-preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 呼叫 DELETE /api/v1/resources/{res_alias}')
def step_delete(context, email, res_alias):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    rid = _resolve_resource_id(context, res_alias)
    response = context.api_client.delete(
        f"/api/v1/resources/{rid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo[f"deleted_resource_id_{res_alias}"] = rid


@when('未認證使用者呼叫 DELETE /api/v1/resources/{res_alias}')
def step_unauth_delete(context, res_alias):
    rid = _resolve_resource_id(context, res_alias)
    response = context.api_client.delete(f"/api/v1/resources/{rid}")
    context.last_response = response


@given('使用者 "{email}" 已硬刪資源 {res_alias}')
def step_already_deleted(context, email, res_alias):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    rid = _resolve_resource_id(context, res_alias)
    response = context.api_client.delete(
        f"/api/v1/resources/{rid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (200, 204), (
        f"前置硬刪失敗: {response.status_code} {response.text}"
    )
    context.memo[f"deleted_resource_id_{res_alias}"] = rid
