"""Given 使用者已開始測驗 — Aggregate Given (precondition)"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus


@given('使用者 "{email}" 已開始測驗 {exam_id:d}')
def step_impl(context, email, exam_id):
    """Ensure exam is IN_PROGRESS for this user (start it via API)."""
    db = context.db_session
    exam_uuid = uuid.UUID(int=exam_id)

    # Check exam status; if READY, start it via API
    exam = db.query(Exam).filter_by(id=exam_uuid).first()
    if exam and exam.status == ExamStatus.READY:
        user_id = context.ids[email]
        token = context.jwt_helper.generate_token(user_id)
        response = context.api_client.post(
            f"/api/v1/exams/{exam_uuid}/start",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [200, 201], \
            f"Failed to start exam: {response.status_code} {response.text}"
        # Refresh session to see changes
        db.expire_all()
    elif exam and exam.status == ExamStatus.IN_PROGRESS:
        pass  # Already in progress
    else:
        raise ValueError(f"Exam {exam_id} not found or invalid status: {exam}")

    # Store current exam_id for subsequent When steps
    context.memo["current_exam_id"] = str(exam_uuid)
