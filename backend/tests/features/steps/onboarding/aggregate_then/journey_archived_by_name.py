"""Then 科目的學習歷程 is_archived 應為 true — Aggregate Then"""

import uuid

from behave import then

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject


@then('科目 "{subject_name}" 的學習歷程 is_archived 應為 true')
def step_impl(context, subject_name):
    db = context.db_session
    db.expire_all()

    # Find email from context
    email = None
    for key in context.ids:
        if "@" in key:
            email = key
            break

    user_uuid = uuid.UUID(context.ids[email])
    subject = db.query(Subject).filter_by(name=subject_name).first()
    assert subject is not None, f"找不到科目 '{subject_name}'"

    journey = db.query(LearningJourney).filter_by(
        user_id=user_uuid, subject_id=subject.id
    ).first()
    assert journey is not None, \
        f"找不到 '{subject_name}' 的學習歷程"
    assert journey.is_archived is True, \
        f"預期 is_archived=True，實際: {journey.is_archived}"
