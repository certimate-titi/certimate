"""Then 回應應包含有效的 CheckMacValue / ReturnURL / OrderResultURL — Read Model"""

import re

from behave import then


@then('回應應包含有效的 CheckMacValue')
def step_impl(context):
    data = context.last_response.json()
    assert "CheckMacValue" in data, (
        f"回應缺少 'CheckMacValue' 欄位，實際欄位: {list(data.keys())}"
    )
    mac = data["CheckMacValue"]
    assert re.fullmatch(r"[A-F0-9]{64}", mac), (
        f"CheckMacValue 應為 64 字元大寫十六進位，實際: {mac}"
    )


@then('回應應包含 ReturnURL 指向後端回呼端點')
def step_return_url(context):
    data = context.last_response.json()
    assert "ReturnURL" in data, (
        f"回應缺少 'ReturnURL' 欄位，實際欄位: {list(data.keys())}"
    )
    assert "callback" in data["ReturnURL"].lower() or "ecpay" in data["ReturnURL"].lower(), (
        f"ReturnURL 應指向回呼端點，實際: {data['ReturnURL']}"
    )


@then('回應應包含 OrderResultURL 指向前端付款結果頁')
def step_order_result_url(context):
    data = context.last_response.json()
    assert "OrderResultURL" in data, (
        f"回應缺少 'OrderResultURL' 欄位，實際欄位: {list(data.keys())}"
    )
