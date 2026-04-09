"""Given 測驗前置狀態 — Aggregate Given"""

import uuid

from behave import given


@given('使用者 "{email}" 準備開始測驗 {exam_id:d}')
def step_impl_exam_ready(context, email, exam_id):
    """確認測驗處於 READY 狀態，準備開始。"""
    from app.models.exam import Exam, ExamStatus
    from app.models.user import User

    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        return
    exam_uuid = uuid.UUID(int=exam_id)
    exam = context.db_session.query(Exam).filter(Exam.id == exam_uuid).first()
    if exam:
        context.memo["current_exam_id"] = str(exam_uuid)
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 已開始測驗 {exam_id:d}，剩餘時間為 {minutes:d} 分鐘')
def step_impl_exam_started_with_time(context, email, exam_id, minutes):
    """確保測驗已開始，並設定剩餘時間 memo（模擬計時器狀態）。"""
    from app.models.exam import Exam, ExamStatus
    from app.models.user import User

    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        return
    exam_uuid = uuid.UUID(int=exam_id)
    context.memo["current_exam_id"] = str(exam_uuid)
    context.memo["current_user_email"] = email
    context.memo["remaining_minutes"] = minutes
    context.memo["remaining_seconds"] = minutes * 60
