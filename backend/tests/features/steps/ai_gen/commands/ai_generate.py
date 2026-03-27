"""When 後端 AI 生成服務開始處理 — Command"""

from behave import when


@when('後端 AI 生成服務開始處理')
def step_impl(context):
    # Ensure we have an exam
    exam_id = context.memo.get("current_exam_id")
    if not exam_id:
        # Need to create an exam via API or directly
        raise KeyError("找不到當前測驗任務 ID，需先提交測驗設定")

    # Find the current user
    email = context.memo.get("current_user_email")
    if not email:
        for key in context.ids:
            if '@' in key:
                email = key
                break

    if email and email in context.ids:
        token = context.jwt_helper.generate_token(context.ids[email])
    else:
        raise KeyError("找不到當前使用者")

    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    context.last_response = response

    if response.status_code in (200, 201):
        data = response.json()
        context.memo["generation_result"] = data
        # Store stage results if available
        if "stages" in data:
            for stage_key, stage_data in data["stages"].items():
                context.memo[f"{stage_key}_output"] = stage_data
