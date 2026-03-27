"""When 使用者選擇分類 — Query (GET)"""

from behave import when


@when('使用者選擇分類 "{category}"')
def step_impl(context, category):
    token = context.memo.get("current_token")
    response = context.api_client.get(
        f"/api/v1/onboarding/subjects?category={category}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
