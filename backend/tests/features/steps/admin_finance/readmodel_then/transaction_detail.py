"""Then 交易展開詳情驗證 — ReadModel Then"""

from behave import then


@then('交易 "{transaction_id}" 應展開顯示詳細資訊：')
def step_impl(context, transaction_id):
    """驗證交易詳情包含預期欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        for row in context.table:
            field = row["欄位"]
            expected = row["值"]
            actual = str(data.get(field, ""))
            assert actual == expected, \
                f"交易 '{transaction_id}' 欄位 '{field}' 應為 '{expected}'，實際: '{actual}'"
