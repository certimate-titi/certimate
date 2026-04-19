"""Given 當月累計用量為 / 當月 X 累計用量為 N — Aggregate Given.

語義為「絕對值」：先刪除該 provider 的所有 ledger 紀錄，再寫入指定金額。
"""

from datetime import datetime, timezone
from decimal import Decimal

from behave import given

from app.models.ai_usage_ledger import AiUsageLedger


_SCOPE_TO_PROVIDER = {
    "AI_ANTHROPIC": "anthropic",
    "AI_GEMINI": "gemini",
    "AI_VOYAGE": "voyage",
}


def _set_ledger_absolute(db, provider: str, target_usd: Decimal):
    """Reset provider's ledger to a single row equal to target_usd."""
    db.query(AiUsageLedger).filter(AiUsageLedger.provider == provider).delete()
    entry = AiUsageLedger(
        provider=provider,
        endpoint="synthetic/test",
        input_tokens=0,
        output_tokens=0,
        cost_usd=target_usd,
        feature="bdd_given",
        billing_source="app",
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)


@given('當月累計用量為：')
def step_impl(context):
    db = context.db_session
    for row in context.table:
        scope = row["scope"]
        provider = _SCOPE_TO_PROVIDER.get(scope)
        if provider is None:
            # GCP_TOTAL 不寫 ledger
            continue
        _set_ledger_absolute(db, provider, Decimal(row["current_usd"]))
    db.commit()


@given('當月 Voyage 累計用量為 {amount} USD')
def step_impl_voyage(context, amount):
    _set_ledger_absolute(context.db_session, "voyage", Decimal(amount))
    context.db_session.commit()


@given('當月 Anthropic 累計用量為 {amount} USD')
def step_impl_anthropic(context, amount):
    _set_ledger_absolute(context.db_session, "anthropic", Decimal(amount))
    context.db_session.commit()


@given('當月 Gemini 累計用量為 {amount} USD')
def step_impl_gemini(context, amount):
    _set_ledger_absolute(context.db_session, "gemini", Decimal(amount))
    context.db_session.commit()


@given('當月 GCP 累計用量為 {amount} USD')
def step_impl_gcp(context, amount):
    from app.services.gcp_billing_service import set_test_override
    set_test_override(Decimal(amount))
    context.memo = getattr(context, "memo", {})
    context.memo["gcp_total_usd"] = Decimal(amount)


@given('本次 embedding 預估成本為 {amount} USD')
def step_impl_estimated_cost(context, amount):
    context.memo = getattr(context, "memo", {})
    context.memo["voyage_estimated_cost"] = Decimal(amount)
