"""Then 測驗狀態應更新為 — Aggregate Then"""

import uuid

from behave import then

from app.models.exam import Exam


@then('測驗 {exam_id:d} 的狀態應更新為 "{status}"')
def step_impl(context, exam_id, status):
    db = context.db_session
    db.expire_all()
    exam_uuid = uuid.UUID(int=exam_id)
    exam = db.query(Exam).filter_by(id=exam_uuid).first()
    assert exam is not None, f"測驗 {exam_id} 不存在"
    actual = exam.status.value if hasattr(exam.status, 'value') else exam.status
    assert actual == status, \
        f"預期測驗狀態為 '{status}'，實際為 '{actual}'"
