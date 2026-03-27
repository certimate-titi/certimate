"""Given 以下綠界交易參數 — Aggregate Given"""

from behave import given


@given('以下綠界交易參數：')
def step_impl(context):
    params = {}
    for row in context.table:
        params[row["欄位"]] = row["值"]
    context.memo["ecpay_params"] = params
