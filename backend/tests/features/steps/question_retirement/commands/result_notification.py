"""When 放榜推送排程 — Command"""

from behave import when


@when('系統執行放榜日推送排程')
def step_impl(context):
    response = context.api_client.post(
        "/api/v1/admin/notifications/result-day",
    )
    context.last_response = response


@when('系統執行提醒排程')
def step_reminder(context):
    response = context.api_client.post(
        "/api/v1/admin/notifications/result-reminder",
    )
    context.last_response = response


@when('系統執行預設處理排程')
def step_default_process(context):
    response = context.api_client.post(
        "/api/v1/admin/notifications/result-default",
    )
    context.last_response = response


@when('系統執行交叉推薦排程')
def step_cross_recommend(context):
    response = context.api_client.post(
        "/api/v1/admin/notifications/cross-recommend",
    )
    context.last_response = response
