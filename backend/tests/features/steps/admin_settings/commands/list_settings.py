"""When 查詢系統設定列表（announcements/feature-flags/model-routing/plan-quotas）— Command"""

from behave import when


def _token_for(context, email):
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    return context.jwt_helper.generate_token(str(user.id))


@when('使用者 "{email}" 查詢系統公告列表')
def step_impl_list_announcements(context, email):
    token = _token_for(context, email)
    context.last_response = context.api_client.get(
        "/api/v1/admin/system-settings/announcements",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('使用者 "{email}" 查詢特性旗標列表')
def step_impl_list_feature_flags(context, email):
    token = _token_for(context, email)
    context.last_response = context.api_client.get(
        "/api/v1/admin/system-settings/feature-flags",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('使用者 "{email}" 查詢 AI 模型路由列表')
def step_impl_list_model_routing(context, email):
    token = _token_for(context, email)
    context.last_response = context.api_client.get(
        "/api/v1/admin/system-settings/model-routing",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('使用者 "{email}" 查詢方案配額列表')
def step_impl_list_plan_quotas(context, email):
    token = _token_for(context, email)
    context.last_response = context.api_client.get(
        "/api/v1/admin/system-settings/plan-quotas",
        headers={"Authorization": f"Bearer {token}"},
    )
