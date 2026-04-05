"""Then 使用者的學習歷程應為活躍狀態 — Aggregate Then"""

import uuid

from behave import then

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject


@then('使用者 "{email}" 的學習歷程 "{subject_name}" 應為活躍狀態')
def step_impl(context, email, subject_name):
    db = context.db_session
    db.expire_all()

    user_uuid = uuid.UUID(context.ids[email])
    subject = db.query(Subject).filter_by(name=subject_name).first()
    assert subject is not None, f"找不到科目 '{subject_name}'"

    journey = db.query(LearningJourney).filter_by(
        user_id=user_uuid, subject_id=subject.id
    ).first()
    assert journey is not None, \
        f"找不到使用者 {email} 的 '{subject_name}' 學習歷程"
    assert journey.is_archived is False, \
        f"預期學習歷程為活躍（is_archived=False），實際: {journey.is_archived}"
