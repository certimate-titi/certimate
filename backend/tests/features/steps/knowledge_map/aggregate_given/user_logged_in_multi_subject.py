"""Given 使用者已登入並擁有多個學科的存取權 — Aggregate Given"""

import uuid

from behave import given

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject


@given('使用者已登入並擁有多個學科的存取權')
def user_logged_in_multi_subject(context):
    db = context.db_session

    # Pick the first user with an email from context.ids
    first_email = None
    for key in context.ids:
        if "@" in key:
            first_email = key
            break
    if not first_email:
        raise KeyError("需要至少一個使用者帳號（帶 Email）")

    user_id = uuid.UUID(context.ids[first_email])

    # Generate JWT token and store in context.memo
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_user_id"] = str(user_id)

    # Ensure user has LearningJourney records for available subjects
    subjects = db.query(Subject).all()
    if len(subjects) < 2:
        raise KeyError("需要至少兩個學科才能測試多學科存取")

    for subject in subjects:
        existing = (
            db.query(LearningJourney)
            .filter_by(user_id=user_id, subject_id=subject.id)
            .first()
        )
        if not existing:
            journey = LearningJourney(
                user_id=user_id,
                subject_id=subject.id,
            )
            db.add(journey)

    db.commit()
