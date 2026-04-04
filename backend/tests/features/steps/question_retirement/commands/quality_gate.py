"""When 系統執行品質閘門檢查 — Command"""

from behave import when


@when('系統執行品質閘門檢查')
def step_impl(context):
    questions_data = context.memo.get("ai_gen_questions_data", [])

    response = context.api_client.post(
        "/api/v1/ai-questions/quality-check",
        json={"questions": questions_data},
    )
    context.last_response = response
