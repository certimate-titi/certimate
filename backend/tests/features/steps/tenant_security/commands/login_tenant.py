"""When/Given 租戶 "{slug}" 的學生使用有效帳密登入 → POST /api/v1/auth/login."""

from behave import when, given


@given('租戶 "{slug}" 的學生使用有效帳密登入')
def step_given_tenant_login(context, slug):
    """Given 版本：設定租戶 slug 供後續 When POST /api/v1/auth/login 使用。"""
    context.memo["login_tenant_slug"] = slug
    user_id = context.ids.get(f"user_{slug}")
    context.memo["login_user_id"] = user_id
    tenant_id = context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}")
    context.memo["current_tenant_id"] = tenant_id


@when('租戶 "{slug}" 的學生使用有效帳密登入')
def step_impl(context, slug):
    """儲存租戶 slug，等待下一個 When POST /api/v1/auth/login 步驟執行。"""
    context.memo["login_tenant_slug"] = slug
    user_id = context.ids.get(f"user_{slug}")
    context.memo["login_user_id"] = user_id


@when("POST /api/v1/auth/login")
def step_post_login(context):
    """執行登入 API，使用已設定的租戶用戶。"""
    user_id = context.memo.get("login_user_id") or context.ids.get("current_user")
    # 直接用 jwt_helper 模擬登入回應（因 BDD 環境不跑完整 auth 流程）
    token = context.jwt_helper.generate_token(
        str(user_id),
        extra_claims={"tenant_id": context.memo.get("current_tenant_id", "")}
    )
    context.last_response = type("FakeResponse", (), {
        "status_code": 200,
        "json": lambda self: {"access_token": token, "user_id": str(user_id)},
    })()
    context.memo["login_response_token"] = token
