"""Then step: 橫幅內容格式應為「目前有 N 位考生正一起奮鬥」，其中 N 為正整數"""

import re

from behave import then


@then('橫幅內容格式應為「目前有 N 位考生正一起奮鬥」，其中 N 為正整數')
def step_impl(context):
    data = context.last_response.json()
    banner = data.get("banner", {})
    message = banner.get("message", "")
    pattern = r"目前有 (\d+) 位考生正一起奮鬥"
    match = re.search(pattern, message)
    assert match, f"Banner message format mismatch: {message}"
    n = int(match.group(1))
    assert n > 0, f"Expected positive integer, got: {n}"
