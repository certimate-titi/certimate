"""Given 使用者有學習歷程於考科 — Aggregate Given"""

import uuid

from behave import given

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject, SubjectCategory
from app.repositories.subject_repository import SubjectRepository, SubjectCategoryRepository


@given('使用者 "{email}" 有學習歷程於考科 "{subject_name}"')
def step_impl(context, email, subject_name):
    db = context.db_session
    subject_repo = SubjectRepository(db)
    cat_repo = SubjectCategoryRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = uuid.UUID(context.ids[email])

    # 建立或取得學科
    subject = subject_repo.find_by_name(subject_name)
    if not subject:
        if "exam_subject_cat" not in context.ids:
            cat = SubjectCategory(name="考試分類")
            cat_repo.save(cat)
            context.ids["exam_subject_cat"] = str(cat.id)
        cat_id = uuid.UUID(context.ids["exam_subject_cat"])
        subject = Subject(name=subject_name, category_id=cat_id)
        subject_repo.save(subject)

    context.ids[f"subject_{subject_name}"] = str(subject.id)

    # 建立學習歷程
    journey = LearningJourney(
        user_id=user_id,
        subject_id=subject.id,
    )
    db.add(journey)
    db.commit()
    db.refresh(journey)

    context.ids[f"journey_{email}_{subject_name}"] = str(journey.id)
    context.memo[f"current_subject_{email}"] = str(subject.id)
