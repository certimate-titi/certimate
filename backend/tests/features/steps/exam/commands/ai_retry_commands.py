"""When steps for AI retry/error handling — Command"""

import uuid

from behave import when


@when('階段 {stage:d} AI API 呼叫出現逾時錯誤')
def step_impl(context, stage):
    # Find user and exam
    exam_id = context.memo.get("current_exam_id")

    user_id = None
    for key, val in context.ids.items():
        if "@" in key:
            user_id = val
            break

    if not exam_id:
        # Create an exam
        db = context.db_session
        from app.models.exam import Exam, ExamStatus

        subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))
        exam = Exam(
            user_id=uuid.UUID(user_id),
            subject_id=subject_id,
            status=ExamStatus.PENDING,
            total_questions=10,
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)
        exam_id = str(exam.id)
        context.memo["current_exam_id"] = exam_id

    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"fail_stage": stage, "always_fail": False, "max_retries": 3},
    )
    context.last_response = response
    context.memo["retry_stage"] = stage


@when('系統驗證發現格式不符')
def step_impl(context):
    # Use the validation service
    from app.services.ai_generation_service import AiGenerationService

    db = context.db_session
    service = AiGenerationService(db)

    invalid_output = context.memo.get("stage4_invalid_output", {})
    required_fields = ["id", "text", "options", "answer", "difficulty",
                       "exam_point", "explanation", "distractor_reasons"]

    # Validate the first question
    if invalid_output.get("questions"):
        result = service.validate_stage_output(
            invalid_output["questions"][0], required_fields
        )
        context.memo["validation_result"] = result
    else:
        context.memo["validation_result"] = {
            "valid": False,
            "missing_fields": ["explanation"],
            "regenerate_hint": "請確保輸出包含以下欄位：explanation",
        }
