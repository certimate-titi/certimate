"""Then 原有科目的學習歷程不受影響 — Aggregate Then"""

import uuid

from behave import then

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject


@then('原有 "{subject_name}" 的學習歷程不受影響')
def step_impl(context, subject_name):
    db = context.db_session
    db.expire_all()

    email = context.memo.get("current_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_uuid = uuid.UUID(context.ids[email])

    # 優先從 context.ids 取已知 subject_id，避免同名 subject（migration seed vs step 建立）導致查錯
    known_subject_id = context.ids.get(f"subject_{subject_name}")
    if known_subject_id:
        subj_ids = [uuid.UUID(known_subject_id)]
    else:
        # fallback：查所有同名 subject
        subjs = db.query(Subject).filter(Subject.name == subject_name).all()
        assert subjs, f"找不到科目 '{subject_name}'"
        subj_ids = [s.id for s in subjs]

    # 只要有任一 subject 對應到使用者的活躍 journey 即可
    journey = (
        db.query(LearningJourney)
        .filter(
            LearningJourney.user_id == user_uuid,
            LearningJourney.subject_id.in_(subj_ids),
            LearningJourney.is_archived == False,  # noqa: E712
        )
        .first()
    )
    assert journey is not None, \
        f"使用者 {email} 的 '{subject_name}' 學習歷程應仍存在"
