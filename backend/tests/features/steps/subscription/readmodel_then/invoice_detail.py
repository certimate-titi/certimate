"""Then — 驗證帳單明細欄位。"""

from behave import then


@then('回應中每筆帳單應包含：')
def step_invoice_detail(context):
    response = context.last_response
    data = response.json()

    invoices = data.get("invoices", data if isinstance(data, list) else [])
    assert len(invoices) > 0, "回應中沒有帳單記錄"

    for row in context.table:
        field = row["欄位"]
        example_value = row["範例值"]

        for inv in invoices:
            assert field in inv, \
                f"帳單記錄缺少欄位 '{field}'，實際欄位: {list(inv.keys())}"
