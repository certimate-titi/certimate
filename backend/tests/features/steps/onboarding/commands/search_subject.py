"""When 使用者在搜尋欄輸入關鍵字 — Query (GET)"""

from behave import when


@when('使用者在搜尋欄輸入 "{keyword}"')
def step_impl(context, keyword):
    token = context.memo.get("current_token")
    response = context.api_client.get(
        f"/api/v1/onboarding/subjects/search?q={keyword}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
