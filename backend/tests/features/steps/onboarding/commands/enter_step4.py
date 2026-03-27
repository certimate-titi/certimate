"""When 使用者進入 Step 4 確認頁 — Query (GET)"""

from behave import when


@when('使用者進入 Step 4 確認頁')
def step_impl(context):
    token = context.memo.get("current_token")

    response = context.api_client.get(
        "/api/v1/onboarding/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
