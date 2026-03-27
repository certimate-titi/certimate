"""Given 系統中有以下交易紀錄 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.transaction import Transaction


@given('系統中有以下交易紀錄：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        transaction_id = row["交易 ID"]
        user_id_key = row["使用者 ID"].strip()
        amount = float(row["金額"])
        plan = row["方案"]
        status = row["狀態"]
        created_at_str = row["交易時間"]

        user_uuid = uuid.UUID(context.ids[user_id_key])
        created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)

        txn = Transaction(
            merchant_trade_no=transaction_id,
            user_id=user_uuid,
            amount=amount,
            target_plan=plan,
            status=status,
            created_at=created_at,
        )
        db.add(txn)
        db.flush()
        context.ids[transaction_id] = str(txn.id)

    db.commit()
