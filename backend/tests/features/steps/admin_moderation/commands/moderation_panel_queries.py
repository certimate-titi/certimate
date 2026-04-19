"""When 前端審核面板查詢（queue/stats/abuse/content-review）— Command"""

from behave import when, then


def _token_for(context, email):
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    return context.jwt_helper.generate_token(str(user.id))


@when('使用者 "{email}" 查詢前端審核佇列')
def step_impl_query_queue(context, email):
    token = _token_for(context, email)
    context.last_response = context.api_client.get(
        "/api/v1/admin/moderation/queue",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('使用者 "{email}" 查詢審核統計')
def step_impl_query_stats(context, email):
    token = _token_for(context, email)
    context.last_response = context.api_client.get(
        "/api/v1/admin/moderation/stats",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('使用者 "{email}" 查詢前端濫用監控')
def step_impl_query_abuse(context, email):
    token = _token_for(context, email)
    context.last_response = context.api_client.get(
        "/api/v1/admin/moderation/abuse",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('使用者 "{email}" 查詢內容審核佇列')
def step_impl_query_content_review(context, email):
    token = _token_for(context, email)
    context.last_response = context.api_client.get(
        "/api/v1/admin/moderation/content-review",
        headers={"Authorization": f"Bearer {token}"},
    )


@then('回應應包含 "{field}" 欄位')
def step_impl_response_has_field(context, field):
    data = context.last_response.json()
    assert field in data, f"回應缺少 '{field}' 欄位；實際欄位: {list(data.keys())}"
