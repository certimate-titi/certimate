"""Then 科目的學習歷程應被封存 — Aggregate Then"""

import uuid

from behave import then

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject


@then('"{subject_name}" 的學習歷程應被封存（非刪除）')
def step_impl(context, subject_name):
    db = context.db_session
    db.expire_all()

    email = context.memo.get("current_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_uuid = uuid.UUID(context.ids[email])

    subj = db.query(Subject).filter_by(name=subject_name).first()
    assert subj is not None, f"找不到科目 '{subject_name}'"

    journey = db.query(LearningJourney).filter_by(
        user_id=user_uuid, subject_id=subj.id
    ).first()
    assert journey is not None, \
        f"找不到使用者 {email} 的 '{subject_name}' 學習歷程"
    assert journey.is_archived is True, \
        f"預期學習歷程 is_archived=True，實際: {journey.is_archived}"
