"""When super-admin / 一般使用者 / 未認證 對 subject hard-delete API 發送請求。"""

from behave import given, when


def _resolve_subject_id(context, subject_alias):
    """alias `subj_01` → context.ids 中的真實 UUID；若不在 dict 就直接當 UUID 字串。"""
    return context.ids.get(subject_alias, subject_alias)


@when('super-admin "{email}" 呼叫 GET /api/v1/subjects/{subject_alias}/delete-preview')
def step_get_preview(context, email, subject_alias):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    sid = _resolve_subject_id(context, subject_alias)
    response = context.api_client.get(
        f"/api/v1/subjects/{sid}/delete-preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('super-admin "{email}" 呼叫 DELETE /api/v1/subjects/{subject_alias}/hard')
def step_super_admin_hard_delete(context, email, subject_alias):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    sid = _resolve_subject_id(context, subject_alias)
    response = context.api_client.delete(
        f"/api/v1/subjects/{sid}/hard",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo[f"deleted_subject_id_{subject_alias}"] = sid


@when('使用者 "{email}" 呼叫 DELETE /api/v1/subjects/{subject_alias}/hard')
def step_user_hard_delete(context, email, subject_alias):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    sid = _resolve_subject_id(context, subject_alias)
    response = context.api_client.delete(
        f"/api/v1/subjects/{sid}/hard",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('未認證使用者呼叫 DELETE /api/v1/subjects/{subject_alias}/hard')
def step_unauth_subject_hard_delete(context, subject_alias):
    sid = _resolve_subject_id(context, subject_alias)
    response = context.api_client.delete(f"/api/v1/subjects/{sid}/hard")
    context.last_response = response


@given('super-admin "{email}" 已硬刪科目 {subject_alias}')
def step_already_deleted(context, email, subject_alias):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    sid = _resolve_subject_id(context, subject_alias)
    response = context.api_client.delete(
        f"/api/v1/subjects/{sid}/hard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (200, 204), (
        f"前置硬刪失敗: {response.status_code} {response.text}"
    )
    context.memo[f"deleted_subject_id_{subject_alias}"] = sid
