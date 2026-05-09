"""Completion Framework — Then (API response assertion) steps.

注意：「回應狀態碼應為 {code:d}」已在 subject_fork/readmodel_then/response_body.py 定義，
此模組不重複定義，直接使用共用 step。
"""

from behave import then


def _body(context) -> dict:
    """取得 JSON 回應 body。"""
    return context.last_response.json()


# ─── 數值斷言 ─────────────────────────────────────────────────────────────

@then('完成度回應 {field} 應為 {value:d}')
def step_field_equals_int(context, field, value):
    body = _body(context)
    actual = body.get(field)
    assert actual == value, f"{field} expected {value}, got {actual}. body={body}"


@then('完成度回應 {field} 應大於 {value:d}')
def step_field_gt(context, field, value):
    body = _body(context)
    actual = body.get(field)
    assert actual > value, f"{field} expected > {value}, got {actual}"


@then('完成度回應 {field} 應小於 {value:d}')
def step_field_lt(context, field, value):
    body = _body(context)
    actual = body.get(field)
    assert actual < value, f"{field} expected < {value}, got {actual}"


# ─── 布林斷言 ─────────────────────────────────────────────────────────────

@then('完成度回應 should_show_marginal_utility_nudge 應為 true')
def step_nudge_true(context):
    body = _body(context)
    val = body.get("should_show_marginal_utility_nudge")
    assert val is True, f"should_show_marginal_utility_nudge expected True, got {val}. body={body}"


@then('完成度回應 should_show_marginal_utility_nudge 應為 false')
def step_nudge_false(context):
    body = _body(context)
    val = body.get("should_show_marginal_utility_nudge")
    assert val is False, f"should_show_marginal_utility_nudge expected False, got {val}. body={body}"


# ─── 徽章斷言 ─────────────────────────────────────────────────────────────

@then('完成度回應 badges_unlocked 應為空陣列')
def step_no_badges(context):
    body = _body(context)
    badges = body.get("badges_unlocked", [])
    assert badges == [], f"Expected empty badges, got {badges}"


@then('完成度回應 badges_unlocked 包含 "{badge_code}"')
def step_badge_in(context, badge_code):
    body = _body(context)
    badges = body.get("badges_unlocked", [])
    assert badge_code in badges, (
        f"Badge '{badge_code}' not found in {badges}. body={body}"
    )
