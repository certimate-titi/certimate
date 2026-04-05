"""Then 使用者的活躍學習歷程不應包含 — Aggregate Then"""

import uuid

from behave import then

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject


@then('使用者 "{email}" 的活躍學習歷程不應包含 "{subject_name}"')
def step_impl(context, email, subject_name):
    db = context.db_session
    db.expire_all()

    user_uuid = uuid.UUID(context.ids[email])
    subject = db.query(Subject).filter_by(name=subject_name).first()
    if not subject:
        return  # Subject not in DB = not in active journeys

    journey = db.query(LearningJourney).filter_by(
        user_id=user_uuid, subject_id=subject.id, is_archived=False
    ).first()
    assert journey is None, \
        f"使用者 {email} 仍有活躍的 '{subject_name}' 學習歷程"
