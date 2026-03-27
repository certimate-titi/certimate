"""Then 回應應包含新建立的 feedback_id — Readmodel Then"""

from behave import then


@then('回應應包含新建立的 feedback_id')
def step_impl(context):
    response = context.last_response
    data = response.json()

    feedback_id = data.get("feedback_id") or data.get("id")
    assert feedback_id is not None and str(feedback_id).strip() != "", \
        f"回應中缺少 feedback_id，實際回應: {data}"
