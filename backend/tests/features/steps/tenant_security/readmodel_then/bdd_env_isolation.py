"""Then test_tenant_id 應不等於 public_b2c 的 UUID & 應為有效的 UUID 格式."""

from behave import then
import uuid
from app.repositories.tenant_repository import PUBLIC_B2C_TENANT_ID


@then("test_tenant_id 應不等於 public_b2c 的 UUID")
def step_impl(context):
    """驗證測試環境的 tenant_id 不是 public_b2c。"""
    test_tenant_id = context.memo.get("test_tenant_id")
    assert test_tenant_id is not None, "test_tenant_id 未設定"
    assert str(test_tenant_id) != PUBLIC_B2C_TENANT_ID, \
        "test_tenant_id 不應等於 public_b2c"


@then("test_tenant_id 應為有效的 UUID 格式")
def step_impl_uuid_format(context):
    """驗證 test_tenant_id 是有效的 UUID 格式。"""
    test_tenant_id = context.memo.get("test_tenant_id")
    assert test_tenant_id is not None, "test_tenant_id 未設定"
    try:
        uuid.UUID(str(test_tenant_id))
    except ValueError:
        assert False, f"test_tenant_id 不是有效的 UUID 格式：{test_tenant_id}"


@then("resources 表中不應有任何 tenant_id = test_tenant 的資料殘留")
def step_impl_no_residual(context):
    """驗證 after_scenario TRUNCATE 後無測試資料殘留。"""
    test_tenant_id = context.memo.get("test_tenant_id")
    if test_tenant_id:
        from app.models.resource import Resource
        try:
            uid = uuid.UUID(str(test_tenant_id))
            count = context.db_session.query(Resource).filter(
                Resource.tenant_id == uid
            ).count()
            assert count == 0, f"仍有 {count} 筆 tenant_id={test_tenant_id} 的資料殘留"
        except ValueError:
            pass  # UUID 解析失敗，跳過


@then('before_scenario 之後 context.test_tenant_id 已設定')
def step_impl_context_set(context):
    """驗證 test_tenant_id 已被設定。"""
    test_tenant_id = getattr(context, "test_tenant_id", None) or context.memo.get("test_tenant_id")
    assert test_tenant_id is not None, "context.test_tenant_id 未設定"
