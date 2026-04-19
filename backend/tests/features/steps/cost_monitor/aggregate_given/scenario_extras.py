"""Given 輔助情境 Given — compound / synonym / failure simulation."""

from decimal import Decimal

from behave import given

from app.models.budget_config import BudgetConfig


@given('AI_VOYAGE 月預算為 {limit:d} USD 且當月已用 {used:d} USD')
def step_impl_compound(context, limit, used):
    from app.models.ai_usage_ledger import AiUsageLedger
    db = context.db_session
    config = db.query(BudgetConfig).filter(BudgetConfig.scope == "AI_VOYAGE").first()
    if config is None:
        config = BudgetConfig(
            scope="AI_VOYAGE",
            monthly_limit_usd=Decimal(limit),
            warning_percent=50,
            degrade_percent=80,
            disable_percent=100,
            gcp_sync_enabled=False,
        )
        db.add(config)
    else:
        config.monthly_limit_usd = Decimal(limit)
    db.add(
        AiUsageLedger(
            provider="voyage",
            endpoint="bdd/synthetic",
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal(used),
            feature="bdd_given",
        )
    )
    db.commit()


@given('AI 功能狀態為 "{state}"')
def step_impl_ai_state(context, state):
    """Set AI_VOYAGE state (代表性 scope) — Feature 33 此 Given 僅用於 Voyage 解除停用情境。"""
    db = context.db_session
    config = db.query(BudgetConfig).filter(BudgetConfig.scope == "AI_VOYAGE").first()
    if config is None:
        config = BudgetConfig(
            scope="AI_VOYAGE",
            monthly_limit_usd=Decimal("50"),
            gcp_sync_enabled=False,
        )
        db.add(config)
    config.current_state = state
    db.commit()


@given('budget_config 中 "{scope}" 尚未同步')
def step_impl_not_synced(context, scope):
    config = (
        context.db_session.query(BudgetConfig)
        .filter(BudgetConfig.scope == scope)
        .first()
    )
    if config is not None:
        config.gcp_budget_resource_name = None
        context.db_session.commit()


@given('GCP Budgets API 暫時無法回應')
def step_impl_gcp_down(context):
    """Inject a failure flag into the in-memory fake adapter via memo.

    The BDD test relies on GcpBudgetSyncService's fake adapter. When we set
    this flag, any subsequent Budget update will see the adapter raise, which
    the service catches and reports as SyncResult(status="failed").

    Since each BudgetService creates its own GcpBudgetSyncService + fake adapter,
    we simulate by monkey-patching the default factory at import time.
    """
    import app.services.gcp_budget_sync_service as gbs

    original_factory = gbs._make_default_adapter

    def _failing_adapter():
        adapter = gbs.InMemoryFakeAdapter()
        adapter.simulate_failure = True
        return adapter

    gbs._make_default_adapter = _failing_adapter
    context.memo = getattr(context, "memo", {})
    context.memo["_gbs_factory_restore"] = original_factory
