"""Then 回應 JWT payload 應包含 "tenant_id" 欄位."""

from behave import then
import base64
import json


def _decode_jwt_payload(token: str) -> dict:
    """解碼 JWT payload（不驗簽名）。"""
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload_b64 = parts[1]
    # 補齊 base64 padding
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    decoded = base64.urlsafe_b64decode(payload_b64)
    return json.loads(decoded)


@then('回應 JWT payload 應包含 "tenant_id" 欄位')
def step_impl(context):
    """驗證回應中的 JWT 包含 tenant_id 欄位。"""
    token = context.memo.get("login_response_token") or context.memo.get("current_token")
    assert token, "找不到 JWT Token"

    payload = _decode_jwt_payload(token)
    assert "tenant_id" in payload, \
        f"JWT payload 應包含 tenant_id，實際 payload: {payload}"


@then('"tenant_id" 值應等於 {slug} 的 UUID')
def step_impl_value(context, slug):
    """驗證 JWT 中的 tenant_id 值等於指定租戶的 UUID。"""
    token = context.memo.get("login_response_token") or context.memo.get("current_token")
    assert token, "找不到 JWT Token"

    payload = _decode_jwt_payload(token)
    tenant_id = context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}")
    assert str(payload.get("tenant_id")) == str(tenant_id), \
        f"JWT tenant_id 不符：期望 {tenant_id}，實際 {payload.get('tenant_id')}"
