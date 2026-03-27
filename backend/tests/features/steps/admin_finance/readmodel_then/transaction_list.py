"""Then 回應中交易紀錄相關驗證 — Readmodel Then"""

from behave import then


@then('回應中應包含交易紀錄列表')
def step_impl(context):
    resp = context.last_response
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "transactions" in data, f"回應缺少 transactions 欄位：{data}"
    assert isinstance(data["transactions"], list), f"transactions 應為 list"


@then('回應中所有交易的狀態應為 "{expected_status}"')
def step_impl_filter(context, expected_status):
    resp = context.last_response
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    transactions = data.get("transactions", [])
    assert len(transactions) > 0, "回應中無交易紀錄"
    for txn in transactions:
        actual = txn.get("status")
        assert actual == expected_status, \
            f"交易 {txn.get('transaction_id')} 狀態應為 '{expected_status}'，實際 '{actual}'"
