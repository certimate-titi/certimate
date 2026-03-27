"""Then 反饋 "..." 的狀態應為 "..." — Aggregate Then"""

from behave import then

from app.models.feedback import Feedback


@then('反饋 "{feedback_id}" 的狀態應為 "{expected_status}"')
def step_impl(context, feedback_id, expected_status):
    db = context.db_session
    db.expire_all()

    feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    assert feedback is not None, f"找不到反饋 '{feedback_id}'"

    assert feedback.status == expected_status, \
        f"反饋 '{feedback_id}' 預期狀態為 '{expected_status}'，實際為 '{feedback.status}'"
