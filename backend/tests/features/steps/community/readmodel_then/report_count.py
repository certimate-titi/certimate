"""Then step: 回應應包含 {n} 份週報"""

from behave import then


@then('回應應包含 {n:d} 份週報')
def step_impl(context, n):
    data = context.last_response.json()
    reports = data.get("reports", [])
    assert len(reports) == n, \
        f"Expected {n} reports, got {len(reports)}: {reports}"
