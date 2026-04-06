"""Then 品質報告驗證 — ReadModel Then"""

from behave import then


@then('coverage_rate 應大於等於 {pct:d}%')
def step_impl_coverage(context, pct):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    data = response.json()
    coverage = data.get("coverage_rate", 0)
    # coverage_rate may be 0-100 or 0.0-1.0
    if isinstance(coverage, float) and coverage <= 1.0:
        coverage = coverage * 100
    assert coverage >= pct, \
        f"預期 coverage_rate >= {pct}%，實際為 {coverage}%"


@then('max_depth 應介於 {min_depth:d} 至 {max_depth:d} 之間')
def step_impl_depth(context, min_depth, max_depth):
    response = context.last_response
    data = response.json()
    actual = data.get("max_depth", 0)
    assert min_depth <= actual <= max_depth, \
        f"預期 max_depth 介於 {min_depth}~{max_depth}，實際為 {actual}"


@then('reliability 應為 "{expected}"（{description}）')
def step_impl_reliability(context, expected, description):
    response = context.last_response
    data = response.json()
    actual = data.get("reliability", "")
    assert actual == expected, \
        f"預期 reliability 為 '{expected}'，實際為 '{actual}'"
