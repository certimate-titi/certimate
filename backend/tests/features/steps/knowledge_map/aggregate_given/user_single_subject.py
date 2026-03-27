"""Given 使用者僅備考單一科目 — Aggregate Given"""

import uuid

from behave import given

from app.models.learning_journey import LearningJourney
from app.repositories.learning_journey_repository import LearningJourneyRepository


@given('使用者 "{email}" 僅備考 "{subject}"')
def step_impl(context, email, subject):
    db = context.db_session
    repo = LearningJourneyRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    if subject not in context.ids:
        raise KeyError(f"找不到科目 '{subject}' 的 ID")

    user_id = uuid.UUID(context.ids[email])
    subject_id = uuid.UUID(context.ids[subject])

    journey = LearningJourney(
        user_id=user_id,
        subject_id=subject_id,
    )
    repo.save(journey)
