"""When 使用者在個人儀表板點擊新增備考科目 — Query (GET)"""

from behave import when


@when('使用者在個人儀表板點擊「+ 新增備考科目」')
def step_impl(context):
    email = context.memo.get("current_email")
    if not email:
        # Try to find from context.ids
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_id = context.ids.get(email)
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token

    response = context.api_client.get(
        "/api/v1/subjects/available",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
