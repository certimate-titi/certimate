"""Then 回應應包含綠界表單參數 — Read Model"""

from behave import then


@then('回應應包含綠界表單參數：')
def step_impl(context):
    response = context.last_response
    assert response.status_code in (200, 201), (
        f"預期成功（2XX），實際 {response.status_code}: {response.text}"
    )

    data = response.json()

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]

        assert field in data, (
            f"回應缺少 '{field}' 欄位，實際欄位: {list(data.keys())}"
        )

        actual = str(data[field])

        # 動態值只驗證存在性和格式
        if expected.startswith("(") and expected.endswith(")"):
            if "長度" in expected:
                assert len(actual) <= 20, (
                    f"MerchantTradeNo 長度應 <= 20，實際: {len(actual)}"
                )
        else:
            assert actual == expected, (
                f"欄位 '{field}' 預期 '{expected}'，實際 '{actual}'"
            )
