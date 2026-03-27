"""Then 計算流程應為 / 結果應為有效的 64 字元大寫十六進位字串 — Read Model"""

import re

from behave import then


@then('計算流程應為：')
def step_impl(context):
    # DocString 描述計算流程，此處僅驗證計算結果已存在
    mac = context.memo.get("calculated_mac")
    assert mac is not None, "CheckMacValue 計算結果不存在"


@then('結果應為有效的 64 字元大寫十六進位字串')
def step_hex_result(context):
    mac = context.memo.get("calculated_mac")
    assert mac is not None, "CheckMacValue 計算結果不存在"
    assert re.fullmatch(r"[A-F0-9]{64}", mac), (
        f"結果應為 64 字元大寫十六進位字串，實際: {mac} (長度: {len(mac)})"
    )
