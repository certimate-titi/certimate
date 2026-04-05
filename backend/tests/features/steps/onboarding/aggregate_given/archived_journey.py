"""Given 使用者有已封存的學習歷程於科目 — Aggregate Given"""

import uuid

from behave import given

from app.models.subject import Subject, SubjectCategory
from app.models.learning_journey import LearningJourney


@given('使用者 "{email}" 有已封存的學習歷程於科目 "{subject_name}"')
def step_impl(context, email, subject_name):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    # Ensure category
    cat = db.query(SubjectCategory).first()
    if not cat:
        cat = SubjectCategory(name="default")
        db.add(cat)
        db.flush()

    # Ensure subject
    subject = db.query(Subject).filter_by(name=subject_name).first()
    if not subject:
        subject = Subject(name=subject_name, category_id=cat.id, available_questions=100)
        db.add(subject)
        db.flush()

    # Create archived journey
    journey = LearningJourney(
        user_id=user_uuid,
        subject_id=subject.id,
        is_archived=True,
    )
    db.add(journey)
    db.commit()
