"""Given 資料庫中有 pending 交易紀錄 — Aggregate Given"""

import uuid
from decimal import Decimal

from behave import given

from app.models.transaction import Transaction


@given('資料庫中有 pending 交易紀錄：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        user_id_key = row["user_id"].strip()
        user_uuid = uuid.UUID(context.ids[user_id_key])

        txn = Transaction(
            user_id=user_uuid,
            merchant_trade_no=row["merchant_trade_no"],
            target_plan=row["target_plan"],
            amount=Decimal(row["amount"]),
            status=row["status"],
            payment_provider="ecpay",
        )
        db.add(txn)

    db.commit()

    # 儲存交易編號到 memo 供後續使用
    for row in context.table:
        trade_no = row["merchant_trade_no"]
        context.memo[f"txn_{trade_no}"] = trade_no
