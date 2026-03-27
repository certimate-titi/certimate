"""Then 回應應包含 N 筆待處理檢舉 — Readmodel Then"""

from behave import then


@then('回應應包含 {count:d} 筆待處理檢舉')
def step_impl(context, count):
    data = context.last_response.json()
    reports = data.get("reports", [])
    assert len(reports) == count, \
        f"應有 {count} 筆待處理檢舉，實際 {len(reports)} 筆: {reports}"
