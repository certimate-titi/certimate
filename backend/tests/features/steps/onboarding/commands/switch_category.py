"""When 使用者切換分類標籤 — Command"""

from behave import when


@when('使用者切換分類標籤至 "{category}"')
def step_impl(context, category):
    """呼叫 API 切換分類標籤（全部或特定分類）。"""
    token = context.memo.get("current_token")
    if category == "全部":
        url = "/api/v1/onboarding/subjects"
    else:
        url = f"/api/v1/onboarding/subjects?category={category}"
    response = context.api_client.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_category"] = category
