"""Given 系統中有以下預算設定 / 當前預算設定為 — Aggregate Given."""

from decimal import Decimal

from behave import given

from app.models.budget_config import BudgetConfig


def _upsert(db, row):
    scope = row["scope"]
    existing = db.query(BudgetConfig).filter(BudgetConfig.scope == scope).first()
    if existing is None:
        existing = BudgetConfig(
            scope=scope,
            monthly_limit_usd=Decimal(row["monthly_limit_usd"]),
            warning_percent=int(row.get("warning_percent", 50)),
            degrade_percent=int(row.get("degrade_percent", 80)),
            disable_percent=int(row.get("disable_percent", 100)),
        )
        # AI_ANTHROPIC / AI_VOYAGE 不同步 GCP
        existing.gcp_sync_enabled = scope in ("AI_GEMINI", "GCP_TOTAL")
        db.add(existing)
    else:
        existing.monthly_limit_usd = Decimal(row["monthly_limit_usd"])
        if "warning_percent" in row.headings:
            existing.warning_percent = int(row["warning_percent"])
        if "degrade_percent" in row.headings:
            existing.degrade_percent = int(row["degrade_percent"])
        if "disable_percent" in row.headings:
            existing.disable_percent = int(row["disable_percent"])
    db.flush()


@given('系統中有以下預算設定：')
def step_impl(context):
    for row in context.table:
        _upsert(context.db_session, row)
    context.db_session.commit()


@given('當前預算設定為：')
def step_impl_current(context):
    for row in context.table:
        _upsert(context.db_session, row)
    context.db_session.commit()


@given('AI_VOYAGE 的 degrade_percent 為 {pct:d}')
def step_impl_set_voyage_degrade(context, pct):
    from app.models.budget_config import BudgetConfig
    db = context.db_session
    config = db.query(BudgetConfig).filter(BudgetConfig.scope == "AI_VOYAGE").first()
    if config is None:
        config = BudgetConfig(
            scope="AI_VOYAGE",
            monthly_limit_usd=Decimal("50"),
            warning_percent=50,
            degrade_percent=pct,
            disable_percent=100,
            gcp_sync_enabled=False,
        )
        db.add(config)
    else:
        config.degrade_percent = pct
    db.commit()


@given('budget_config 中 "{scope}" 的 gcp_budget_resource_name 為 null')
def step_impl_sync_null(context, scope):
    config = (
        context.db_session.query(BudgetConfig)
        .filter(BudgetConfig.scope == scope)
        .first()
    )
    if config is not None:
        config.gcp_budget_resource_name = None
        context.db_session.commit()


@given('budget_config 中 "{scope}" 已有 gcp_budget_resource_name')
def step_impl_sync_existing(context, scope):
    config = (
        context.db_session.query(BudgetConfig)
        .filter(BudgetConfig.scope == scope)
        .first()
    )
    if config is not None and not config.gcp_budget_resource_name:
        config.gcp_budget_resource_name = (
            f"billingAccounts/FAKE/budgets/pre-existing-{scope}"
        )
        context.db_session.commit()


@given('budget_config 各 scope 已有 gcp_budget_resource_name')
def step_impl_sync_all(context):
    for c in context.db_session.query(BudgetConfig).all():
        if c.gcp_sync_enabled and not c.gcp_budget_resource_name:
            c.gcp_budget_resource_name = (
                f"billingAccounts/FAKE/budgets/pre-existing-{c.scope}"
            )
    context.db_session.commit()
