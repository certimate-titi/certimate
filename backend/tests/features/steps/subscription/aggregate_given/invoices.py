"""Given 系統中有以下帳單記錄 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.invoice import Invoice


@given('系統中有以下帳單記錄：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        invoice_id = row["帳單 ID"]
        user_id_key = row["使用者 ID"].strip()
        amount = float(row["金額"])
        status = row["狀態"]
        created_at_str = row["建立時間"]

        user_uuid = uuid.UUID(context.ids[user_id_key])
        created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)

        invoice = Invoice(
            user_id=user_uuid,
            stripe_invoice_id=invoice_id,
            amount=amount,
            plan=context.memo.get(f"user_{user_id_key}_plan", "FREE"),
            status=status,
            created_at=created_at,
        )
        db.add(invoice)
        db.flush()
        context.ids[invoice_id] = str(invoice.id)

    db.commit()
