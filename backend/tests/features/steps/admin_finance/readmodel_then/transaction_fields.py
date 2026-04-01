"""Then 回應中每筆交易應包含指定欄位 — Readmodel Then"""

from behave import then


@then('回應中每筆交易應包含：')
def step_impl(context):
    resp = context.last_response
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    transactions = data.get("transactions", [])
    assert len(transactions) > 0, "回應中無交易紀錄"

    required_fields = [row["欄位"] for row in context.table]
    for txn in transactions:
        for field in required_fields:
            assert field in txn, \
                f"交易 {txn.get('transaction_id', '?')} 缺少欄位 '{field}'，實際欄位：{list(txn.keys())}"
