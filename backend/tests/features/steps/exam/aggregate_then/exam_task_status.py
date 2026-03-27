"""Then 系統應建立測驗任務，初始狀態為 — Aggregate Then"""

import uuid

from behave import then

from app.models.exam import Exam
from app.repositories.exam_repository import ExamRepository


@then('系統應建立測驗任務，初始狀態為 "{status}"')
def step_impl(context, status):
    db = context.db_session

    # 從回應中取得 exam_id，或從 DB 查最新的
    response = context.last_response
    data = response.json()
    exam_id_str = data.get("exam_id")

    if exam_id_str:
        exam = ExamRepository(db).find_by_id(uuid.UUID(exam_id_str))
    else:
        # 找到第一個使用者的最新 exam
        for key, val in context.ids.items():
            if '@' in key:
                exam = ExamRepository(db).find_latest_by_user(uuid.UUID(val))
                break

    assert exam is not None, "找不到測驗任務"

    exam_status = exam.status.value if hasattr(exam.status, 'value') else exam.status
    assert exam_status == status, (
        f"測驗狀態應為 '{status}'，但得到 '{exam_status}'"
    )
