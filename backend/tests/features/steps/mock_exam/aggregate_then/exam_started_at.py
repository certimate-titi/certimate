"""Then 測驗應記錄開始時間 — Aggregate Then"""

import uuid

from behave import then

from app.models.exam import Exam


@then('測驗 {exam_id:d} 應記錄開始時間')
def step_impl(context, exam_id):
    db = context.db_session
    db.expire_all()
    exam_uuid = uuid.UUID(int=exam_id)
    exam = db.query(Exam).filter_by(id=exam_uuid).first()
    assert exam is not None, f"測驗 {exam_id} 不存在"
    assert exam.started_at is not None, \
        f"測驗 {exam_id} 的 started_at 應不為 None"
