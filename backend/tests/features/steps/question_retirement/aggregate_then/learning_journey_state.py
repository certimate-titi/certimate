"""Then 學習歷程狀態驗證 — Aggregate Then"""

import uuid
from datetime import date, timedelta

from behave import then
from app.models.learning_journey import LearningJourney


@then('學習歷程的 exam_result_status 應為 "{status}"')
def step_exam_result(context, status):
    db = context.db_session
    journey_id = context.memo.get("current_journey_id")
    assert journey_id, "找不到學習歷程 ID"

    journey = db.query(LearningJourney).filter_by(id=uuid.UUID(journey_id)).first()
    assert journey is not None, f"學習歷程 {journey_id} 不存在"
    assert journey.exam_result_status == status, \
        f"exam_result_status 預期 '{status}'，實際 '{journey.exam_result_status}'"


@then('學習歷程的 exam_result_status 應自動設為 "{status}"')
def step_auto_exam_result(context, status):
    db = context.db_session
    journey_id = context.memo.get("current_journey_id")
    assert journey_id, "找不到學習歷程 ID"

    journey = db.query(LearningJourney).filter_by(id=uuid.UUID(journey_id)).first()
    assert journey is not None, f"學習歷程 {journey_id} 不存在"
    assert journey.exam_result_status == status, \
        f"exam_result_status 預期自動設為 '{status}'，實際 '{journey.exam_result_status}'"


@then('data_expiry_date 應設為今天加 {days:d} 天')
def step_expiry_date(context, days):
    db = context.db_session
    journey_id = context.memo.get("current_journey_id")
    assert journey_id, "找不到學習歷程 ID"

    journey = db.query(LearningJourney).filter_by(id=uuid.UUID(journey_id)).first()
    assert journey is not None, f"學習歷程 {journey_id} 不存在"

    expected = date.today() + timedelta(days=days)
    assert journey.data_expiry_date == expected, \
        f"data_expiry_date 預期 '{expected}'，實際 '{journey.data_expiry_date}'"


@then('學習歷程的 exam_result_status 應更新為 "{status}"')
def step_updated_result(context, status):
    db = context.db_session
    journey_id = context.memo.get("current_journey_id")
    assert journey_id, "找不到學習歷程 ID"

    journey = db.query(LearningJourney).filter_by(id=uuid.UUID(journey_id)).first()
    assert journey is not None, f"學習歷程 {journey_id} 不存在"
    assert journey.exam_result_status == status, \
        f"exam_result_status 預期 '{status}'，實際 '{journey.exam_result_status}'"


@then('exam_date 應更新為 "{date_str}"')
def step_exam_date(context, date_str):
    db = context.db_session
    journey_id = context.memo.get("current_journey_id")
    assert journey_id, "找不到學習歷程 ID"

    journey = db.query(LearningJourney).filter_by(id=uuid.UUID(journey_id)).first()
    assert journey is not None
    expected = date.fromisoformat(date_str)
    assert journey.exam_date == expected, \
        f"exam_date 預期 '{expected}'，實際 '{journey.exam_date}'"


@then('result_date 應更新為 "{date_str}"')
def step_result_date(context, date_str):
    db = context.db_session
    journey_id = context.memo.get("current_journey_id")
    assert journey_id, "找不到學習歷程 ID"

    journey = db.query(LearningJourney).filter_by(id=uuid.UUID(journey_id)).first()
    assert journey is not None
    expected = date.fromisoformat(date_str)
    assert journey.result_date == expected, \
        f"result_date 預期 '{expected}'，實際 '{journey.result_date}'"


@then('學習歷程的 result_date 應更新為 "{date_str}"')
def step_lj_result_date(context, date_str):
    db = context.db_session
    journey_id = context.memo.get("current_journey_id")
    assert journey_id, "找不到學習歷程 ID"

    journey = db.query(LearningJourney).filter_by(id=uuid.UUID(journey_id)).first()
    assert journey is not None
    expected = date.fromisoformat(date_str)
    assert journey.result_date == expected, \
        f"result_date 預期 '{expected}'，實際 '{journey.result_date}'"


@then('data_expiry_date 應清除')
def step_expiry_cleared(context):
    db = context.db_session
    journey_id = context.memo.get("current_journey_id")
    assert journey_id, "找不到學習歷程 ID"

    journey = db.query(LearningJourney).filter_by(id=uuid.UUID(journey_id)).first()
    assert journey is not None
    assert journey.data_expiry_date is None, \
        f"data_expiry_date 應為 NULL，實際 '{journey.data_expiry_date}'"


@then('軟刪除中的 AI 題應恢復（若在 90 天內）')
def step_restored(context):
    db = context.db_session
    from app.models.question import Question

    question_ids = context.memo.get("ai_question_ids", [])
    for qid in question_ids:
        q = db.query(Question).filter_by(id=uuid.UUID(qid)).first()
        if q:
            assert q.retired_at is None, \
                f"AI 題 {qid} retired_at 應被清除（恢復），實際 '{q.retired_at}'"
