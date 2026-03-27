"""Given 系統中有以下退款申請 — Aggregate Given"""

import uuid

from behave import given

from app.models.refund import Refund


@given('系統中有以下退款申請：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        refund_id = row["退款 ID"]
        user_id_key = row["使用者 ID"].strip()
        transaction_id = row["交易 ID"]
        amount = float(row["金額"])
        status = row["狀態"]

        user_uuid = uuid.UUID(context.ids[user_id_key])

        refund = Refund(
            refund_id=refund_id,
            user_id=user_uuid,
            transaction_id=transaction_id,
            amount=amount,
            status=status,
        )
        db.add(refund)
        db.flush()
        context.ids[refund_id] = str(refund.id)

    db.commit()
