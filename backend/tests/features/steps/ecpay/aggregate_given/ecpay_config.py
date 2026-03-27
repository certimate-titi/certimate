"""Given 系統中有以下綠界金流設定 — Aggregate Given"""

from behave import given


@given('系統中有以下綠界金流設定：')
def step_impl(context):
    config = {}
    for row in context.table:
        config[row["設定"]] = row["值"]
    context.memo["ecpay_config"] = config
