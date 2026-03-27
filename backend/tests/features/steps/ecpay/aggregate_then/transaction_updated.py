"""Then 交易紀錄應更新為 / 交易紀錄狀態不應變更 — Aggregate Then"""

from behave import then

from app.models.transaction import Transaction


@then('交易紀錄 "{trade_no}" 應更新為：')
def step_impl(context, trade_no):
    db = context.db_session
    db.expire_all()

    txn = db.query(Transaction).filter_by(merchant_trade_no=trade_no).first()
    assert txn is not None, f"找不到交易紀錄 '{trade_no}'"

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]
        actual = getattr(txn, field, None)

        if actual is None:
            assert False, f"Transaction 沒有欄位 '{field}'"

        assert str(actual) == expected, (
            f"交易 '{trade_no}' 的 {field} 預期 '{expected}'，實際 '{actual}'"
        )


@then('交易紀錄狀態不應變更')
def step_no_change(context):
    pre_status = context.memo.get("pre_callback_status")
    if not pre_status:
        return  # 沒有記錄前置狀態，跳過

    db = context.db_session
    db.expire_all()

    txn = db.query(Transaction).filter_by(status="pending").first()
    if txn:
        assert txn.status == pre_status, (
            f"交易狀態不應變更，預期 '{pre_status}'，實際 '{txn.status}'"
        )


@then('交易紀錄 "{trade_no}" 的 status 應為 "{expected_status}"')
def step_status(context, trade_no, expected_status):
    db = context.db_session
    db.expire_all()

    txn = db.query(Transaction).filter_by(merchant_trade_no=trade_no).first()
    assert txn is not None, f"找不到交易紀錄 '{trade_no}'"
    assert txn.status == expected_status, (
        f"交易 '{trade_no}' 的 status 預期 '{expected_status}'，實際 '{txn.status}'"
    )
