"""When 使用者在測驗設定頁面選擇學科 — Query"""

from behave import when


@when('使用者在測驗設定頁面頂部選擇學科 "{subject}"')
def step_impl(context, subject):
    # 取得第一個使用者的 token
    token = None
    for key, val in context.ids.items():
        if '@' in key:
            token = context.jwt_helper.generate_token(val)
            break

    response = context.api_client.get(
        f"/api/v1/exams/resources?subject={subject}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
