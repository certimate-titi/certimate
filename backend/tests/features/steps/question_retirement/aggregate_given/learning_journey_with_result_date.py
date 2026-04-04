"""Given 使用者有學習歷程於科目（含 result_date）— Aggregate Given"""

import uuid
from datetime import date

from behave import given
from app.models.learning_journey import LearningJourney
from app.repositories.learning_journey_repository import LearningJourneyRepository
from app.repositories.subject_repository import SubjectRepository


@given('使用者 "{email}" 有學習歷程於科目 "{subject_name}"：')
def step_impl(context, email, subject_name):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)

    # 解析 DataTable 欄位
    fields = {}
    for row in context.table:
        fields[row["欄位"]] = row["值"]

    journey = LearningJourney(
        user_id=user_id,
        subject_id=subject.id,
        exam_date=date.fromisoformat(fields["exam_date"]) if "exam_date" in fields else None,
        result_date=date.fromisoformat(fields["result_date"]) if "result_date" in fields else None,
        exam_result_status=fields.get("exam_result_status"),
    )

    lj_repo = LearningJourneyRepository(db)
    saved = lj_repo.save(journey)

    context.memo[f"learning_journey_{email}_{subject_name}"] = str(saved.id)
    context.memo["current_journey_id"] = str(saved.id)


@given('使用者 "{email}" 有學習歷程於科目 "{subject_name}"')
def step_without_table(context, email, subject_name):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)

    lj_repo = LearningJourneyRepository(db)
    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    if not journey:
        journey = LearningJourney(
            user_id=user_id,
            subject_id=subject.id,
        )
        journey = lj_repo.save(journey)

    context.memo[f"learning_journey_{email}_{subject_name}"] = str(journey.id)
    context.memo["current_journey_id"] = str(journey.id)
