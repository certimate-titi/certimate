"""嘗試呼叫 purge_tenant_data 腳本，目標為 tenant_id = "00000000-0000-0000-0000-000000b2cb2c"."""

from behave import given
from app.repositories.tenant_repository import PUBLIC_B2C_TENANT_ID


@given('嘗試呼叫 purge_tenant_data 腳本，目標為 tenant_id = "{tenant_id}"')
def step_impl(context, tenant_id):
    """設定嘗試刪除 public_b2c 的目標 tenant_id。"""
    context.memo["target_purge_tenant_id"] = tenant_id
    # 確認目標是 public_b2c
    assert tenant_id == PUBLIC_B2C_TENANT_ID or tenant_id == "00000000-0000-0000-0000-000000b2cb2c", \
        f"預期是 public_b2c UUID，實際是 {tenant_id}"
