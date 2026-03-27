"""When step: 系統觸發每週學習報告生成排程"""

from behave import when


@when('系統觸發每週學習報告生成排程')
def step_impl(context):
    activities = context.memo.get("activities", {})
    context.last_response = context.api_client.post(
        "/api/v1/community/weekly-report/generate",
        json={"activities": activities},
    )
