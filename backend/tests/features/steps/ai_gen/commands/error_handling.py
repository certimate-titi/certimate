"""When 錯誤處理相關操作 — Command"""

from behave import when


@when('階段 2 AI API 呼叫出現逾時錯誤')
def step_stage2_timeout(context):
    exam_id = context.memo.get("current_exam_id")
    assert exam_id, "找不到當前測驗任務 ID"

    # Find a user token
    token = None
    for key, val in context.ids.items():
        if '@' in key:
            token = context.jwt_helper.generate_token(val)
            context.memo["current_user_id"] = val
            break
    assert token, "找不到使用者 token"

    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"fail_stage": 2, "always_fail": False, "max_retries": 3},
    )
    context.last_response = response

    if response.status_code in (200, 201):
        context.memo["generation_result"] = response.json()


@when('系統驗證發現格式不符')
def step_validate_format(context):
    from app.services.ai_generation_service import AiGenerationService
    db = context.db_session
    service = AiGenerationService(db)

    invalid_output = context.memo.get("stage_4_invalid_output", {})
    required_fields = [
        "id", "text", "options", "answer", "difficulty",
        "exam_point", "explanation", "distractor_reasons",
    ]

    result = service.validate_stage_output(invalid_output, required_fields)
    context.memo["validation_result"] = result
