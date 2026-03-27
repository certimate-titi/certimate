"""Given 使用者的某科目考試日期為空 — Aggregate Given"""

import uuid

from behave import given

from app.models.learning_journey import LearningJourney


@given('使用者 "{email}" 的 {subject_name} 考試日期為空')
def step_impl(context, email, subject_name):
    db = context.db_session
    journey_key = f"journey_{email}_{subject_name}"

    if journey_key in context.ids:
        journey_id = uuid.UUID(context.ids[journey_key])
        journey = db.query(LearningJourney).filter_by(id=journey_id).first()
        if journey:
            journey.exam_date = None
            db.commit()
