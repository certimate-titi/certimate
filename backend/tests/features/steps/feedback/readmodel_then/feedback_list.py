"""Then 回應應包含 N 筆反饋 / 回應共包含 N 筆反饋 — Readmodel Then"""

import re

from behave import then


@then('回應應包含 {count:d} 筆反饋（{feedback_ids}）')
def step_impl(context, count, feedback_ids):
    response = context.last_response
    data = response.json()

    items = data if isinstance(data, list) else data.get("items", data.get("feedbacks", []))
    assert len(items) == count, \
        f"預期 {count} 筆反饋，實際 {len(items)} 筆"

    # Parse expected feedback IDs like "FB-001、FB-003"
    expected_ids = [fid.strip() for fid in re.split(r'[、,]', feedback_ids)]
    actual_ids = [item.get("feedback_id") for item in items]

    for expected_id in expected_ids:
        assert expected_id in actual_ids, \
            f"預期包含反饋 '{expected_id}'，實際清單: {actual_ids}"


@then('回應共包含 {count:d} 筆反饋')
def step_impl(context, count):
    response = context.last_response
    data = response.json()

    items = data if isinstance(data, list) else data.get("items", data.get("feedbacks", []))
    assert len(items) == count, \
        f"預期 {count} 筆反饋，實際 {len(items)} 筆"
