"""Then Onboarding 狀態相關 — ReadModel Then"""

import uuid

from behave import then

from app.models.user import User
from app.models.learning_journey import LearningJourney


@then('回應應標記 Onboarding 為未完成')
def step_impl(context):
    response = context.last_response
    data = response.json()
    assert data.get("onboarding_completed") is False, \
        f"預期 Onboarding 未完成，實際 {data.get('onboarding_completed')}"


@then('使用者 "{email}" 的 Onboarding 狀態應為已完成')
def step_impl_completed(context, email):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    db.refresh(user)
    assert user.onboarding_completed is True, \
        f"預期 Onboarding 已完成，實際 {user.onboarding_completed}"


@then('使用者 "{email}" 應有 {count:d} 個學習歷程')
def step_impl_journeys(context, email, count):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    journeys = db.query(LearningJourney).filter_by(
        user_id=user_uuid, is_archived=False
    ).all()
    assert len(journeys) == count, \
        f"預期 {count} 個學習歷程，實際 {len(journeys)}"
