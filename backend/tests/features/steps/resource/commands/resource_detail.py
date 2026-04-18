"""When 資源詳情查詢與處理觸發 — Commands"""

from behave import when


@when('使用者 "{email}" 查詢資源詳情')
def step_impl_get_own_resource(context, email):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"
    resource_id = context.memo.get("last_resource_id")
    assert resource_id, "memo 無 last_resource_id（先執行「已上傳資源」的 Given）"
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/resources/{resource_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢該資源詳情')
def step_impl_get_other_resource(context, email):
    step_impl_get_own_resource(context, email)


@when('使用者 "{email}" 觸發資源處理')
def step_impl_trigger_process(context, email):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"
    resource_id = context.memo.get("last_resource_id")
    assert resource_id, "memo 無 last_resource_id"
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.post(
        f"/api/v1/resources/{resource_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 觸發不存在資源的處理')
def step_impl_trigger_process_missing(context, email):
    import uuid as _uuid
    user_id = context.ids.get(email)
    assert user_id is not None
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.post(
        f"/api/v1/resources/{_uuid.uuid4()}/process",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
