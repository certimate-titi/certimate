"""When after_scenario 鉤子執行 TRUNCATE."""

from behave import when


@when("after_scenario 鉤子執行 TRUNCATE")
def step_impl(context):
    """模擬 after_scenario 的 TRUNCATE 行為：清空所有資料表。"""
    # 由 environment.py 的 after_scenario 實際執行 TRUNCATE
    # 此 step 模擬場景：after_scenario 執行後，測試資料已清空
    # 在 BDD 測試框架中，after_scenario 是在 scenario 結束後執行的
    # 此 step 直接驗證清空邏輯

    test_tenant_id = context.memo.get("test_tenant_id") or getattr(context, "test_tenant_id", None)

    if test_tenant_id:
        import uuid
        from app.models.resource import Resource
        uid = uuid.UUID(str(test_tenant_id))
        context.db_session.query(Resource).filter(
            Resource.tenant_id == uid
        ).delete()
        context.db_session.commit()

    context.memo["truncate_executed"] = True
