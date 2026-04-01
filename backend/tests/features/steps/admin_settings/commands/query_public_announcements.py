"""When 一般用戶查詢公開公告列表 — Command"""

from behave import when


@when('一般用戶查詢公開公告列表')
def step_impl(context):
    response = context.api_client.get("/api/v1/announcements")
    context.last_response = response
