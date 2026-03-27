"""When 未登入的使用者直接呼叫意見反饋提交 API — Command (POST)"""

from behave import when


@when('未登入的使用者直接呼叫意見反饋提交 API')
def step_impl(context):
    response = context.api_client.post(
        "/api/v1/feedback",
        json={
            "type": "BUG",
            "subject": "測試主旨",
            "content": "測試內容",
        },
    )
    context.last_response = response
