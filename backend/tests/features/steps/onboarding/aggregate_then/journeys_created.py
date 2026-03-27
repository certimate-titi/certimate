"""Then 系統應為每個備考科目各建立一份獨立的學習歷程 — Aggregate Then"""

import uuid

from behave import then

from app.models.learning_journey import LearningJourney


@then('系統應為每個備考科目各建立一份獨立的學習歷程')
def step_impl(context):
    db = context.db_session
    email = context.memo.get("current_email")
    user_uuid = uuid.UUID(context.ids[email])

    journeys = db.query(LearningJourney).filter_by(
        user_id=user_uuid, is_archived=False
    ).all()

    assert len(journeys) > 0, "預期至少建立一個學習歷程，但找不到任何歷程"

    subject_ids = [str(j.subject_id) for j in journeys]
    assert len(subject_ids) == len(set(subject_ids)), \
        f"學習歷程的科目應各不相同，實際: {subject_ids}"
