"""When/Then — Cloud Tasks Worker endpoint BDD steps."""

import uuid

from behave import when, then


@when('Cloud Tasks 推送 process-resource payload 資源 {resource_id:d} 給 Worker')
def step_push_valid_payload(context, resource_id):
    """推送有效的 process-resource payload 到 Worker endpoint。"""
    res_uuid = str(uuid.UUID(int=resource_id))

    # 取得任意使用者 ID（從 context.ids 取第一個可用的）
    user_id = list(context.ids.values())[0] if context.ids else str(uuid.uuid4())

    payload = {
        "resource_id": res_uuid,
        "user_id": user_id,
        "tenant_id": "00000000-0000-0000-0000-000000b2cb2c",
    }

    # 本地測試設定 BACKGROUND_PROCESSOR=inline，跳過 OIDC 驗證
    import os
    os.environ["BACKGROUND_PROCESSOR"] = "inline"

    response = context.api_client.post(
        "/api/v1/tasks/process-resource",
        json=payload,
    )
    context.last_response = response


@when('Cloud Tasks 推送不存在的 resource_id 給 Worker')
def step_push_nonexistent_resource(context):
    """推送不存在的 resource_id 到 Worker endpoint，預期 404。"""
    import os
    os.environ["BACKGROUND_PROCESSOR"] = "inline"

    payload = {
        "resource_id": str(uuid.uuid4()),  # 隨機不存在的 UUID
        "user_id": str(uuid.uuid4()),
        "tenant_id": "00000000-0000-0000-0000-000000b2cb2c",
    }
    response = context.api_client.post(
        "/api/v1/tasks/process-resource",
        json=payload,
    )
    context.last_response = response


# Note: '@then HTTP 狀態碼應為 {status_code:d}' 已於 ecpay/readmodel_then/http_status.py
# 既有定義，沿用即可，不再重複註冊（避免 AmbiguousStep）。

@then('回應中 ok 應為 true')
def step_check_ok_true(context):
    """驗證回應 JSON 中 ok 為 true。"""
    data = context.last_response.json()
    assert data.get("ok") is True, f"預期 ok=true，實際回應: {data}"


@then('回應中應包含 resource_id')
def step_check_response_has_resource_id(context):
    """驗證回應中包含 resource_id 欄位。"""
    data = context.last_response.json()
    assert "resource_id" in data or "id" in data, (
        f"回應中缺少 resource_id 欄位: {data}"
    )


@then('操作失敗，HTTP 狀態為 {status_code:d}')
def step_operation_failed_with_status(context, status_code):
    """驗證操作失敗且 HTTP 狀態碼符合預期。"""
    assert context.last_response.status_code == status_code, (
        f"預期 HTTP {status_code}，實際為 {context.last_response.status_code}. "
        f"Body: {context.last_response.text}"
    )
