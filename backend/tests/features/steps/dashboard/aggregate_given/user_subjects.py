"""Given 使用者備考科目設定 — Aggregate Given"""

import uuid
from datetime import date

from behave import given

from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney


def _ensure_category(db, context):
    if "default_cat" not in context.ids:
        cat = SubjectCategory(name="default")
        db.add(cat)
        db.flush()
        context.ids["default_cat"] = str(cat.id)
    return uuid.UUID(context.ids["default_cat"])


def _ensure_subject(db, context, subject_name, cat_id):
    key = f"subject_{subject_name}"
    if key not in context.ids:
        subj = Subject(name=subject_name, category_id=cat_id)
        db.add(subj)
        db.flush()
        context.ids[key] = str(subj.id)
    return uuid.UUID(context.ids[key])


@given('使用者 "{email}" 備考以下科目：')
def step_impl(context, email):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    cat_id = _ensure_category(db, context)

    for row in context.table:
        subject_name = row["科目"]
        exam_date_str = row.get("考試日期", "")

        subject_id = _ensure_subject(db, context, subject_name, cat_id)

        exam_date = date.fromisoformat(exam_date_str) if exam_date_str else None
        journey = LearningJourney(
            user_id=user_uuid,
            subject_id=subject_id,
            exam_date=exam_date,
        )
        db.add(journey)

    db.commit()


@given('使用者 "{email}" 尚未設定任何備考科目')
def step_impl_no_subjects(context, email):
    """Remove all journeys for the user (override Background subjects)."""
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    journeys = db.query(LearningJourney).filter_by(user_id=user_uuid).all()
    for j in journeys:
        db.delete(j)
    db.commit()


@given('使用者 "{email}" 目前在儀表板檢視 "{subject_name}"')
def step_impl_viewing(context, email, subject_name):
    """No-op: the subject context is passed via query param in the When step."""
    context.memo["current_subject"] = subject_name
