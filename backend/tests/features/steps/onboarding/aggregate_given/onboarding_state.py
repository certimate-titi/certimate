"""Given 使用者 Onboarding 狀態 — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User
from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney


@given('使用者 "{email}" 已完成 Onboarding')
def step_impl(context, email):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    user.onboarding_completed = True
    db.commit()


@given('使用者 "{email}" 有備考科目 "{subject_name}"')
def step_impl_subject(context, email, subject_name):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    if "default_cat" not in context.ids:
        cat = SubjectCategory(name="default_cat")
        db.add(cat)
        db.flush()
        context.ids["default_cat"] = str(cat.id)

    cat_id = uuid.UUID(context.ids["default_cat"])

    subj_key = f"subject_{subject_name}"
    if subj_key not in context.ids:
        subj = Subject(name=subject_name, category_id=cat_id, available_questions=100)
        db.add(subj)
        db.flush()
        context.ids[subj_key] = str(subj.id)

    subject_id = uuid.UUID(context.ids[subj_key])

    journey = LearningJourney(
        user_id=user_uuid,
        subject_id=subject_id,
    )
    db.add(journey)
    db.commit()
