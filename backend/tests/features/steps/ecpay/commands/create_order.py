"""When 使用者建立付款訂單 — Command"""

from behave import when


@when('使用者 "{email}" 建立付款訂單，目標方案為 "{plan}"')
def step_impl(context, email, plan):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/ecpay/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_plan": plan},
    )
    context.last_response = response
