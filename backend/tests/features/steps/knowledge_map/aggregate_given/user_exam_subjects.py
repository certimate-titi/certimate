"""Given 使用者備考多個科目 — Aggregate Given"""

import uuid

from behave import given

from app.models.learning_journey import LearningJourney
from app.repositories.learning_journey_repository import LearningJourneyRepository


@given('使用者 "{email}" 備考 "{subject1}" 與 "{subject2}"')
def step_impl(context, email, subject1, subject2):
    db = context.db_session
    repo = LearningJourneyRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = uuid.UUID(context.ids[email])

    for subject_name in [subject1, subject2]:
        if subject_name not in context.ids:
            raise KeyError(f"找不到科目 '{subject_name}' 的 ID")

        subject_id = uuid.UUID(context.ids[subject_name])
        journey = LearningJourney(
            user_id=user_id,
            subject_id=subject_id,
        )
        repo.save(journey)
