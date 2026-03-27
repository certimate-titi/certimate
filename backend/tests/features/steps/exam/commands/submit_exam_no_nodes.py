"""When 使用者提交測驗設定（未勾選節點）— Command"""

from behave import when


@when('使用者 "{email}" 提交測驗設定，未勾選任何知識節點，題數為 {count:d}')
def step_impl(context, email, count):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": [],
            "question_count": count,
        },
    )
    context.last_response = response
