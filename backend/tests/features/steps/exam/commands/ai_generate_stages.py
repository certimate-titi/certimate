"""When 後端 AI 生成服務依序完成各階段 — Command"""

from behave import when


@when('後端 AI 生成服務依序完成各階段')
def step_impl(context):
    # 模擬 AI 生成完成 — 在紅燈階段只需準備 context
    # 實際 SSE 推送在綠燈階段實作
    exam_id = context.memo.get("current_exam_id")
    if not exam_id:
        raise KeyError("找不到當前測驗任務 ID")

    token = None
    for key, val in context.ids.items():
        if '@' in key:
            token = context.jwt_helper.generate_token(val)
            break

    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/generate",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
