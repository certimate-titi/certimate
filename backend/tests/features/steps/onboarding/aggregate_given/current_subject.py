"""Given 使用者目前備考科目（一個或兩個）— Aggregate Given"""

import uuid

from behave import given, use_step_matcher

from app.models.user import User
from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney


def _ensure_subject(context, subject_name):
    """Ensure a subject exists in DB, return its UUID."""
    db = context.db_session
    subj_key = f"subject_{subject_name}"
    if subj_key in context.ids:
        return uuid.UUID(context.ids[subj_key])

    if "default_cat" not in context.ids:
        cat = SubjectCategory(name="default_cat")
        db.add(cat)
        db.flush()
        context.ids["default_cat"] = str(cat.id)

    cat_id = uuid.UUID(context.ids["default_cat"])
    subj = Subject(name=subject_name, category_id=cat_id)
    db.add(subj)
    db.flush()
    context.ids[subj_key] = str(subj.id)
    return subj.id


def _create_journey(context, email, subject_name):
    """Create a learning journey for user + subject."""
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    subject_id = _ensure_subject(context, subject_name)

    user = db.query(User).filter_by(id=user_uuid).first()
    user.onboarding_completed = True

    journey = LearningJourney(user_id=user_uuid, subject_id=subject_id)
    db.add(journey)
    db.flush()
    context.ids[f"journey_{email}_{subject_name}"] = str(journey.id)


use_step_matcher("re")


@given('使用者 "(?P<email>[^"]+)" 目前備考 "(?P<subject1>[^"]+)" 和 "(?P<subject2>[^"]+)"')
def step_two_subjects(context, email, subject1, subject2):
    _create_journey(context, email, subject1)
    _create_journey(context, email, subject2)
    context.db_session.commit()


@given('使用者 "(?P<email>[^"]+)" 目前備考 "(?P<subject>[^"]+)"')
def step_one_subject(context, email, subject):
    _create_journey(context, email, subject)
    context.db_session.commit()


use_step_matcher("parse")
