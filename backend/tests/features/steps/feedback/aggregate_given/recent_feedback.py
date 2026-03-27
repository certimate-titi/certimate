"""Given 使用者 "..." 於 N 分鐘前已提交主旨為 "..." 的意見反饋 — Aggregate Given"""

from datetime import datetime, timedelta, timezone

from behave import given

from app.models.feedback import Feedback


@given('使用者 "{email}" 於 {minutes:d} 分鐘前已提交主旨為 "{subject}" 的意見反饋')
def step_impl(context, email, minutes, subject):
    db = context.db_session
    user_uuid = context.ids.get(email)
    assert user_uuid is not None, f"找不到使用者 '{email}' 的 UUID"

    created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    feedback = Feedback(
        feedback_id=f"FB-RECENT-{email[:5]}",
        user_id=user_uuid,
        type="BUG",
        subject=subject,
        content="重複提交測試用反饋內容",
        status="PENDING",
        created_at=created_at,
    )
    db.add(feedback)
    db.commit()

    context.ids[f"recent_feedback_{email}"] = str(feedback.id)
