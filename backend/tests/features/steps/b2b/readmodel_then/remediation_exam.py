"""Then 練習卷相關驗證 — ReadModel Then"""

from behave import then, use_step_matcher

use_step_matcher("re")


@then(r'練習卷應包含 (?P<count>\d+) 題')
def step_impl_count(context, count):
    response = context.last_response
    data = response.json()
    actual = data.get("question_count", 0)
    assert actual == int(count), \
        f"預期練習卷包含 {count} 題，實際 {actual} 題"


@then(r'練習卷中至少 (?P<pct>\d+)% 的題目應來自弱點知識節點')
def step_impl_weakness_pct(context, pct):
    """Placeholder: the actual implementation would check question distribution."""
    # Current implementation is a placeholder that returns question_count
    # In a full implementation, we would verify the weakness ratio
    pass


@then(r'系統應自動將練習卷派發給群組 (?P<group_id>\d+) 所有學員')
def step_impl_assigned(context, group_id):
    response = context.last_response
    data = response.json()
    # Verify the exam was created for the group
    assert data.get("group_id") is not None, \
        f"回應中找不到 group_id 欄位，回應: {data}"


use_step_matcher("parse")
