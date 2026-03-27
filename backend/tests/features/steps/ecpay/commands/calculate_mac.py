"""When 系統計算 CheckMacValue — Command"""

import hashlib
import urllib.parse

from behave import when


@when('系統以 HashKey "{hash_key}" 和 HashIV "{hash_iv}" 計算 CheckMacValue')
def step_impl(context, hash_key, hash_iv):
    params = context.memo.get("ecpay_params", {})

    # ECPay SHA256 CheckMacValue 計算流程
    # 1. 依照 key 升冪排序
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    # 2. 前綴 HashKey=, 後綴 &HashIV=
    raw = f"HashKey={hash_key}&" + "&".join(f"{k}={v}" for k, v in sorted_params) + f"&HashIV={hash_iv}"
    # 3. URL Encode（小寫）
    encoded = urllib.parse.quote_plus(raw).lower()
    # 4. SHA256 後轉大寫
    mac = hashlib.sha256(encoded.encode("utf-8")).hexdigest().upper()

    context.memo["calculated_mac"] = mac
