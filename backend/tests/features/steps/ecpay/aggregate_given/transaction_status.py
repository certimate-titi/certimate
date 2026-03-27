"""Given 交易紀錄的 status 已為 — Aggregate Given"""

import uuid
from decimal import Decimal

from behave import given

from app.models.transaction import Transaction


@given('交易紀錄 "{trade_no}" 的 status 已為 "{status}"')
def step_impl(context, trade_no, status):
    db = context.db_session

    txn = db.query(Transaction).filter_by(merchant_trade_no=trade_no).first()
    if txn:
        txn.status = status
    else:
        # 建立一筆帶有指定 status 的交易紀錄
        # 使用第一個使用者作為 owner
        first_user_key = next(iter(context.ids))
        user_uuid = uuid.UUID(context.ids[first_user_key])
        txn = Transaction(
            user_id=user_uuid,
            merchant_trade_no=trade_no,
            target_plan="PRO_199",
            amount=Decimal("199"),
            status=status,
            payment_provider="ecpay",
        )
        db.add(txn)

    db.commit()
    context.memo[f"txn_{trade_no}"] = trade_no
    context.memo["last_callback_trade_no"] = trade_no
