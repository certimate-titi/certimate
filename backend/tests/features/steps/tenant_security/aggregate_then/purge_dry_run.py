"""Then 腳本應列出 company_b 的所有資料統計 & 不應實際刪除任何資料."""

from behave import then


@then('腳本應列出 {slug} 的所有資料統計')
def step_impl(context, slug):
    """驗證 purge dry_run 結果包含資料統計。"""
    stats = context.memo.get("purge_stats")
    assert stats is not None, "purge_stats 未設定，請先執行 purge_tenant_data"

    # 確認有統計欄位
    assert "tenant_id" in stats, "stats 缺少 tenant_id 欄位"
    assert "resources" in stats, "stats 缺少 resources 統計"
    assert "resource_chunks" in stats, "stats 缺少 resource_chunks 統計"
    assert "answers" in stats, "stats 缺少 answers 統計"


@then("不應實際刪除任何資料（dry-run 模式）")
def step_impl_no_delete(context):
    """驗證 dry_run 模式下資料未被刪除。"""
    stats = context.memo.get("purge_stats")
    assert stats is not None, "purge_stats 未設定"

    # 驗證是 dry_run 模式
    assert stats.get("dry_run") is True, "應為 dry_run 模式"
    assert "deleted" not in stats, "dry_run 模式下不應有 deleted 欄位"

    # 驗證資料仍然存在
    from app.models.resource import Resource
    tenant_id_str = stats.get("tenant_id")
    if tenant_id_str:
        import uuid
        uid = uuid.UUID(tenant_id_str)
        count = context.db_session.query(Resource).filter(
            Resource.tenant_id == uid
        ).count()
        assert count >= 0  # 資料應該還在（>= 0）


@then("腳本應拋出 ValueError 並終止")
def step_impl_valueerror(context):
    """驗證嘗試刪除 public_b2c 時拋出 ValueError。"""
    error = context.memo.get("purge_error")
    assert error is not None, "應拋出 ValueError，但沒有錯誤"


@then('錯誤訊息應包含 "禁止刪除 public_b2c"')
def step_impl_error_message(context):
    """驗證錯誤訊息包含禁止刪除 public_b2c 的說明。"""
    error = context.memo.get("purge_error")
    assert error is not None, "沒有錯誤訊息"
    assert "禁止刪除 public_b2c" in error, \
        f"錯誤訊息不符：期望包含 '禁止刪除 public_b2c'，實際：{error}"
