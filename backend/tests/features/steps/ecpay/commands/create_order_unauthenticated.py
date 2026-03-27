"""When 未認證用戶發送建立付款訂單請求 — Command"""

from behave import when


@when('未認證用戶發送建立付款訂單請求，目標方案為 "{plan}"')
def step_impl(context, plan):
    response = context.api_client.post(
        "/api/v1/ecpay/create-order",
        json={"target_plan": plan},
    )
    context.last_response = response
