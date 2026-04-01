"""When 使用者查看營運趨勢圖表 — Command (GET)"""

from behave import when


@when('使用者 "{email}" 查看營運趨勢圖表，時間範圍為 "{range_param}"')
def step_impl(context, email, range_param):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/admin/dashboard/charts",
        params={"range": range_param},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
