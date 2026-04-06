"""Then steps — 學員詳情報告回應驗證."""
from behave import then


@then('回應應包含 strengths 列表（分數 >= 70 的能力節點）')
def step_response_has_strengths(context):
    """Verify response contains strengths list."""

    resp = context.last_response.json()
    assert "strengths" in resp, f"Response missing 'strengths': {resp.keys()}"
    assert isinstance(resp["strengths"], list)


@then('回應應包含 weaknesses 列表（分數 < 50 的能力節點）')
def step_response_has_weaknesses(context):
    """Verify response contains weaknesses list."""

    resp = context.last_response.json()
    assert "weaknesses" in resp, f"Response missing 'weaknesses': {resp.keys()}"
    assert isinstance(resp["weaknesses"], list)
