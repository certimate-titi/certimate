"""Given 使用者已建立付款訂單 — Aggregate Given"""

import uuid
from decimal import Decimal

from behave import given

from app.models.transaction import Transaction


# 方案價格對照
_PLAN_PRICES = {
    "PRO_199": 199,
    "PRO_PLUS_399": 399,
    "ULTRA_1599": 1599,
}


@given('使用者 "{email}" 已建立 {plan} 付款訂單')
def step_impl(context, email, plan):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    trade_no = f"CRT{plan}_{email[:4].upper()}"
    if len(trade_no) > 20:
        trade_no = trade_no[:20]

    amount = _PLAN_PRICES.get(plan, 199)

    txn = Transaction(
        user_id=user_uuid,
        merchant_trade_no=trade_no,
        target_plan=plan,
        amount=Decimal(amount),
        status="pending",
        payment_provider="ecpay",
    )
    db.add(txn)
    db.commit()

    context.memo["last_pending_trade_no"] = trade_no
    context.memo["last_pending_email"] = email
    context.memo["last_pending_plan"] = plan
