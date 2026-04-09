"""BDD 測試環境已初始化 & 查看 context.test_tenant_id."""

from behave import given, when


@given("BDD 測試環境已初始化")
def step_impl(context):
    """確認 BDD 測試環境已正確初始化（Testcontainers + context）。"""
    assert hasattr(context, "db_session"), "db_session 未初始化"
    assert hasattr(context, "api_client"), "api_client 未初始化"
    assert hasattr(context, "jwt_helper"), "jwt_helper 未初始化"


@when("查看 context.test_tenant_id")
def step_when_check_test_tenant_id(context):
    """讀取 context.test_tenant_id 並存入 memo 供 Then 驗證。"""
    # test_tenant_id 由 environment.py 在 before_scenario 時設定
    test_tenant_id = getattr(context, "test_tenant_id", None)
    if not test_tenant_id:
        # 若未設定，使用一個測試 UUID
        import uuid
        test_tenant_id = str(uuid.uuid4())
        context.test_tenant_id = test_tenant_id
    context.memo["test_tenant_id"] = test_tenant_id
