"""租戶 "{slug}" 已解約，系統標記為待清除 (@ignore scenario)."""

from behave import given


@given('租戶 "{slug}" 已解約，系統標記為待清除')
def step_impl(context, slug):
    """將租戶標記為 is_active=False（解約狀態）。"""
    from app.repositories.tenant_repository import TenantRepository

    tenant_repo = TenantRepository(context.db_session)
    tenant_id = context.ids.get(slug)

    if not tenant_id:
        raise KeyError(f"找不到租戶 '{slug}'，請先在 Background 中建立")

    tenant_repo.mark_inactive(tenant_id)
    context.memo["decommissioned_tenant_id"] = tenant_id
    context.memo["decommissioned_slug"] = slug
