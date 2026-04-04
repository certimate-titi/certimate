"""Then 系統應建立 N 個新學員帳號 — Aggregate Then"""

from behave import then, use_step_matcher

use_step_matcher("re")


@then(r'系統應建立 (?P<count>\d+) 個新學員帳號，方案為 "(?P<plan>[^"]+)"')
def step_impl_with_plan(context, count, plan):
    response = context.last_response
    data = response.json()
    actual = data.get("created_users", 0)
    assert actual >= int(count), \
        f"預期建立至少 {count} 個帳號，實際建立 {actual} 個"


use_step_matcher("parse")


@then('系統應建立 {count:d} 個新學員帳號')
def step_impl(context, count):
    response = context.last_response
    data = response.json()
    actual = data.get("created_users", 0)
    assert actual == count, \
        f"預期建立 {count} 個帳號，實際建立 {actual} 個"
