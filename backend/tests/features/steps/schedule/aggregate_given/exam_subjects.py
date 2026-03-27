"""Given 使用者的備考科目設定 — Aggregate Given"""

import uuid
from datetime import date

from behave import given

from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney, SelfAssessedLevel


LEVEL_MAP = {
    "beginner": SelfAssessedLevel.BEGINNER,
    "intermediate": SelfAssessedLevel.INTERMEDIATE,
    "advanced": SelfAssessedLevel.ADVANCED,
}


@given('使用者 "{email}" 的備考科目設定如下：')
def step_impl(context, email):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    # Create default category if needed
    if "default_cat" not in context.ids:
        cat = SubjectCategory(name="default_cat")
        db.add(cat)
        db.flush()
        context.ids["default_cat"] = str(cat.id)

    cat_id = uuid.UUID(context.ids["default_cat"])

    for row in context.table:
        subject_name = row["科目"]
        exam_date_str = row["考試日期"]
        level_raw = row["自評程度"]

        # Create subject
        subj_key = f"subject_{subject_name}"
        if subj_key not in context.ids:
            subj = Subject(name=subject_name, category_id=cat_id)
            db.add(subj)
            db.flush()
            context.ids[subj_key] = str(subj.id)

        subject_id = uuid.UUID(context.ids[subj_key])

        exam_date = date.fromisoformat(exam_date_str) if exam_date_str and exam_date_str != "null" else None

        journey = LearningJourney(
            user_id=user_uuid,
            subject_id=subject_id,
            exam_date=exam_date,
            self_assessed_level=LEVEL_MAP.get(level_raw, SelfAssessedLevel.BEGINNER),
        )
        db.add(journey)
        db.flush()
        context.ids[f"journey_{email}_{subject_name}"] = str(journey.id)

    db.commit()
