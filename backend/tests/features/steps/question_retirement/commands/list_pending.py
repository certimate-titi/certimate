"""When 使用者查詢待確認放榜清單 — Command"""

from behave import when


@when('使用者 "{email}" 查詢待確認放榜清單')
def step_list_pending(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        "/api/v1/learning-journeys/pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
