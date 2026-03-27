"""Given 使用者已完成 Onboarding 且目前有 N 個備考科目 — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User
from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney


@given('使用者 "{email}" 已完成 Onboarding 且目前有 {count:d} 個備考科目')
def step_impl(context, email, count):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_uuid).first()
    user.onboarding_completed = True

    # Ensure a default category exists
    if "default_cat" not in context.ids:
        cat = SubjectCategory(name="default_cat")
        db.add(cat)
        db.flush()
        context.ids["default_cat"] = str(cat.id)

    cat_id = uuid.UUID(context.ids["default_cat"])

    # Create N subjects and journeys
    for i in range(count):
        subj_name = f"Subject_{i+1}"
        subj = Subject(name=subj_name, category_id=cat_id)
        db.add(subj)
        db.flush()
        context.ids[f"subject_{subj_name}"] = str(subj.id)

        journey = LearningJourney(user_id=user_uuid, subject_id=subj.id)
        db.add(journey)

    db.commit()
