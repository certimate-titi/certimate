"""Then 回應中不應包含反饋 "..." — Readmodel Then"""

import re

from behave import then


@then('回應中不應包含反饋 "{feedback_id}"（屬於 {other_email}）')
def step_impl(context, feedback_id, other_email):
    response = context.last_response
    data = response.json()

    items = data if isinstance(data, list) else data.get("items", data.get("feedbacks", []))
    actual_ids = [item.get("feedback_id") for item in items]

    assert feedback_id not in actual_ids, \
        f"回應不應包含反饋 '{feedback_id}'（屬於 {other_email}），但實際包含了"
