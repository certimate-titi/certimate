"""Then 系統應建立新的反饋紀錄，狀態為 "..." — Readmodel Then"""

from behave import then


@then('系統應建立新的反饋紀錄，狀態為 "{expected_status}"')
def step_impl(context, expected_status):
    response = context.last_response
    data = response.json()

    # The response should contain the created feedback with the expected status
    status = data.get("status")
    assert status == expected_status, \
        f"預期反饋狀態為 '{expected_status}'，實際為 '{status}'"

    # Store the feedback_id for subsequent steps
    feedback_id = data.get("feedback_id")
    if feedback_id:
        context.memo["last_created_feedback_id"] = feedback_id
