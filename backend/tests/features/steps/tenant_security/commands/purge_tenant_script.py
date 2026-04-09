"""When 執行 purge_tenant_data.py --tenant-id {slug} --dry-run (@ignore scenario)."""

from behave import when


@when('執行 purge_tenant_data.py --tenant-id {slug} --dry-run')
def step_impl(context, slug):
    """呼叫 TenantRepository.purge_tenant_data() 的 dry_run 模式。"""
    from app.repositories.tenant_repository import TenantRepository

    tenant_repo = TenantRepository(context.db_session)
    tenant_id = context.ids.get(slug) or context.memo.get("decommissioned_tenant_id")

    if not tenant_id:
        raise KeyError(f"找不到租戶 '{slug}' 的 ID")

    stats = tenant_repo.purge_tenant_data(tenant_id=tenant_id, dry_run=True)
    context.memo["purge_stats"] = stats
    context.memo["purge_dry_run"] = True


@when("腳本執行")
def step_script_execute(context):
    """執行 purge_tenant_data 腳本（for 禁止刪除 public_b2c 場景）。"""
    from app.repositories.tenant_repository import TenantRepository, PUBLIC_B2C_TENANT_ID

    tenant_repo = TenantRepository(context.db_session)
    try:
        tenant_repo.purge_tenant_data(tenant_id=PUBLIC_B2C_TENANT_ID, dry_run=False)
        context.memo["purge_error"] = None
    except ValueError as e:
        context.memo["purge_error"] = str(e)
