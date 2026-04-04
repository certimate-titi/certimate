"""Then 機構 N 的每月附加費用應為 NT$X — Aggregate Then"""

from behave import then, use_step_matcher

use_step_matcher("re")


@then(r'機構 (?P<inst_id>\d+) 的每月附加費用應為 NT\$(?P<amount>\d+)')
def step_impl(context, inst_id, amount):
    response = context.last_response
    data = response.json()
    actual = data.get("monthly_surcharge", 0)
    assert actual == int(amount), \
        f"預期每月附加費用 NT${amount}，實際為 NT${actual}"


use_step_matcher("parse")
