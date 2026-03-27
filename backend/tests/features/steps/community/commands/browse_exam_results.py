"""When step: 使用者 "{email}" 瀏覽測驗結果頁面"""

from behave import when


@when('使用者 "{email}" 瀏覽測驗結果頁面')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.get(
        "/api/v1/community/exam-results/coaching",
        headers={"Authorization": f"Bearer {token}"},
    )
