"""Then 結果應包含 — ReadModel Then"""

from behave import then


FIELD_MAP = {
    "得分": "score",
    "合格狀態": "pass_status",
    "合格分數": "passing_score",
    "與上次比較": "comparison",
}


@then('結果應包含：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    for row in context.table:
        field_cn = row["欄位"]
        expected = row["值"]
        field_en = FIELD_MAP.get(field_cn, field_cn)
        actual = str(data.get(field_en, ""))
        assert actual == expected, \
            f"結果欄位 '{field_cn}' ({field_en}) 應為 '{expected}'，實際為 '{actual}'，回應: {data}"
