"""When 後端 AI 成功生成考卷 — Command"""

from behave import when


@when('後端 AI 成功生成考卷')
def step_impl(context):
    # 模擬 AI 成功完成生成
    # 在紅燈階段，先前的 submit_exam API 應已回傳 exam_id
    # 呼叫完成生成的 API
    response = context.last_response
    if response and response.status_code in [200, 201]:
        data = response.json()
        exam_id = data.get("exam_id", context.memo.get("current_exam_id"))
        context.memo["current_exam_id"] = exam_id

    # 標記生成完成（供後續 Then 驗證）
    context.memo["ai_generation_complete"] = True
