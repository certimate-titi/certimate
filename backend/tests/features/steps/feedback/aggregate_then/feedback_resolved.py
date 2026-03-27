"""Then 反饋紀錄應包含 resolved_at 時間戳記 — Aggregate Then"""

from behave import then

from app.models.feedback import Feedback


@then('反饋紀錄應包含 resolved_at 時間戳記')
def step_impl(context):
    db = context.db_session
    db.expire_all()

    # Get the feedback ID from the last response or the most recently updated feedback
    response = context.last_response
    data = response.json()
    feedback_id_str = data.get("feedback_id")

    if feedback_id_str:
        feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id_str).first()
    else:
        # Fallback: find the most recently updated RESOLVED feedback
        feedback = (
            db.query(Feedback)
            .filter(Feedback.status == "RESOLVED")
            .order_by(Feedback.updated_at.desc())
            .first()
        )

    assert feedback is not None, "找不到已解決的反饋紀錄"
    assert feedback.resolved_at is not None, \
        f"反饋 '{feedback.feedback_id}' 缺少 resolved_at 時間戳記"
