"""When 使用者未選擇任何備考科目並嘗試進入下一步 — Command"""

from behave import when


@when('使用者未選擇任何備考科目並嘗試進入下一步')
def step_impl(context):
    token = context.memo.get("current_token")
    response = context.api_client.post(
        "/api/v1/onboarding/next",
        headers={"Authorization": f"Bearer {token}"},
        json={"step": 2, "subjects": []},
    )
    context.last_response = response
