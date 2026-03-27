"""When 系統偵測到結束時間已到達 — Command (POST, System Event)"""

from behave import when


@when('系統偵測到結束時間已到達')
def step_impl(context):
    response = context.api_client.post(
        "/api/v1/admin/maintenance-schedules/check-end",
    )
    context.last_response = response
