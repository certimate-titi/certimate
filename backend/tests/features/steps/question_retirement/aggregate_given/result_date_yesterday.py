"""Given 放榜日為昨天 / 已確認結果 — Aggregate Given"""

import uuid
from datetime import date, timedelta

from behave import given

from app.models.learning_journey import LearningJourney
from app.repositories.learning_journey_repository import LearningJourneyRepository
from app.repositories.subject_repository import SubjectRepository


@given('使用者 "{email}" 的科目 "{subject_name}" 放榜日為昨天')
def step_result_date_yesterday(context, email, subject_name):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject = SubjectRepository(db).find_by_name(subject_name)
    lj_repo = LearningJourneyRepository(db)

    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    yesterday = date.today() - timedelta(days=1)
    if journey:
        journey.result_date = yesterday
        journey.exam_result_status = None
        db.commit()
    else:
        journey = LearningJourney(
            user_id=user_id,
            subject_id=subject.id,
            result_date=yesterday,
        )
        journey = lj_repo.save(journey)

    context.memo[f"learning_journey_{email}_{subject_name}"] = str(journey.id)


@given('使用者 "{email}" 已確認科目 "{subject_name}" 考試結果為 "{status}"')
def step_already_confirmed(context, email, subject_name, status):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject = SubjectRepository(db).find_by_name(subject_name)
    lj_repo = LearningJourneyRepository(db)

    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    if not journey:
        journey = LearningJourney(
            user_id=user_id,
            subject_id=subject.id,
            result_date=date.today() - timedelta(days=1),
        )
        journey = lj_repo.save(journey)

    journey.exam_result_status = status
    db.commit()
    context.memo[f"learning_journey_{email}_{subject_name}"] = str(journey.id)
