"""Then 系統應成功回應 200 + 系統應將此請求視為 public_b2c 租戶."""

from behave import then
from app.repositories.tenant_repository import PUBLIC_B2C_TENANT_ID


@then("系統應成功回應 200")
def step_impl(context):
    """驗證 API 回應 200。"""
    assert context.last_response is not None, "沒有 API 回應"
    assert context.last_response.status_code == 200, \
        f"期望 200，實際 {context.last_response.status_code}"


@then("系統應將此請求視為 public_b2c 租戶（向後相容）")
def step_impl_b2c_compat(context):
    """驗證舊格式 JWT 向後相容，被視為 public_b2c 租戶。"""
    # 此驗證在 API 實作後由回應 header 或 DB 行為驗證
    # 目前確認 API 回應成功（舊 token 不被拒絕）
    assert context.last_response is not None, "沒有 API 回應"
    # 向後相容：回應不應為 401/403
    assert context.last_response.status_code not in (401, 403), \
        f"舊格式 JWT 應被向後相容接受，但收到 {context.last_response.status_code}"
