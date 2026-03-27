"""Then 資料庫中應新增一筆交易紀錄 — Aggregate Then"""

import uuid

from behave import then

from app.models.transaction import Transaction


@then('資料庫中應新增一筆交易紀錄：')
def step_impl(context):
    db = context.db_session

    expected = {}
    for row in context.table:
        expected[row["欄位"]] = row["值"]

    user_id_key = expected.get("user_id", "").strip()
    user_uuid = uuid.UUID(context.ids[user_id_key])

    txn = db.query(Transaction).filter_by(user_id=user_uuid).order_by(
        Transaction.created_at.desc()
    ).first()

    assert txn is not None, "資料庫中未找到交易紀錄"

    if "target_plan" in expected:
        assert txn.target_plan == expected["target_plan"], (
            f"預期 target_plan='{expected['target_plan']}'，實際: '{txn.target_plan}'"
        )
    if "amount" in expected:
        assert str(int(txn.amount)) == expected["amount"], (
            f"預期 amount={expected['amount']}，實際: {txn.amount}"
        )
    if "status" in expected:
        assert txn.status == expected["status"], (
            f"預期 status='{expected['status']}'，實際: '{txn.status}'"
        )
    if "payment_provider" in expected:
        assert txn.payment_provider == expected["payment_provider"], (
            f"預期 payment_provider='{expected['payment_provider']}'，實際: '{txn.payment_provider}'"
        )
