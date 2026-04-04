"""Then 回應應包含 1 至 3 條建議 / 每條建議應包含 — ReadModel Then"""

from behave import then, use_step_matcher

use_step_matcher("re")


@then(r'回應應包含 (?P<min_count>\d+) 至 (?P<max_count>\d+) 條建議')
def step_impl(context, min_count, max_count):
    response = context.last_response
    data = response.json()
    suggestions = data.get("suggestions", [])
    assert int(min_count) <= len(suggestions) <= int(max_count), \
        f"預期 {min_count}-{max_count} 條建議，實際 {len(suggestions)} 條"


use_step_matcher("parse")


@then('每條建議應包含：')
def step_impl_fields(context):
    response = context.last_response
    data = response.json()
    suggestions = data.get("suggestions", [])

    required_fields = [row["欄位"] for row in context.table]

    for s in suggestions:
        for field in required_fields:
            assert field in s, \
                f"建議中找不到欄位 '{field}'，實際: {list(s.keys())}"
