"""租戶 "{slug}" 的學生已登入，JWT 含 tenant_id."""

from behave import given


@given('租戶 "{slug}" 的學生已登入，JWT 含 tenant_id')
def step_impl(context, slug):
    """設定目前操作的租戶 + 生成含 tenant_id 的 JWT。"""
    tenant_id = context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}")
    user_id = context.ids.get(f"user_{slug}")

    if not tenant_id:
        raise KeyError(f"找不到租戶 '{slug}'，請先在 Background 中建立")
    if not user_id:
        raise KeyError(f"找不到租戶 '{slug}' 的學生，請先在 Background 中建立")

    # 生成含 tenant_id 的 JWT
    token = context.jwt_helper.generate_token(user_id, extra_claims={"tenant_id": tenant_id})
    context.memo["current_token"] = token
    context.memo["current_tenant_id"] = tenant_id
    context.memo["current_user_id"] = user_id
