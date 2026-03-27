"""Given 使用者在 Step 4 確認頁 — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User
from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney


@given('使用者 "{email}" 在 Step 4 確認頁')
def step_impl(context, email):
    db = context.db_session
    user_id = context.ids[email]
    user_uuid = uuid.UUID(user_id)
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_email"] = email

    # Ensure the user has at least one subject selected (simulate Step 2 completion)
    existing = db.query(LearningJourney).filter_by(
        user_id=user_uuid, is_archived=False
    ).count()

    if existing == 0:
        # Create a default subject and journey
        if "default_cat" not in context.ids:
            cat = SubjectCategory(name="default_cat")
            db.add(cat)
            db.flush()
            context.ids["default_cat"] = str(cat.id)

        cat_id = uuid.UUID(context.ids["default_cat"])

        # Use a subject from the categories if available
        subj = db.query(Subject).first()
        if not subj:
            subj = Subject(name="Default Subject", category_id=cat_id)
            db.add(subj)
            db.flush()

        journey = LearningJourney(user_id=user_uuid, subject_id=subj.id)
        db.add(journey)
        db.commit()
