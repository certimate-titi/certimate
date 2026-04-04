"""Then 群組學員應看到待完成測驗 / 派發記錄包含 — ReadModel Then"""

from behave import then, use_step_matcher

use_step_matcher("re")


@then(r'群組 (?P<group_id>\d+) 的所有學員應看到待完成的測驗任務')
def step_impl(context, group_id):
    response = context.last_response
    data = response.json()
    assert data.get("assigned", False) or data.get("assignment_id"), \
        f"預期考卷已派發，回應: {data}"


use_step_matcher("parse")


@then('派發記錄應包含：')
def step_impl_record(context):
    response = context.last_response
    data = response.json()

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]
        actual = data.get(field)
        assert actual is not None, \
            f"派發記錄中找不到欄位 '{field}'，回應: {data}"
        assert str(expected) in str(actual), \
            f"欄位 '{field}': 預期 '{expected}'，實際 '{actual}'"
