"""When step: 系統執行低谷偵測排程"""

from behave import when


@when('系統執行低谷偵測排程')
def step_impl(context):
    today = context.memo.get("today")
    current_date = today.isoformat() if today else "2026-03-25"
    context.last_response = context.api_client.post(
        "/api/v1/community/valley-detection/run",
        json={"current_date": current_date},
    )
