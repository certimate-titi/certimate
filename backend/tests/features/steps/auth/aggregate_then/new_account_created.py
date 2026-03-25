from behave import then
from app.repositories.user_repository import UserRepository


STATUS_MAP = {
    "待驗證": "pending",
    "已啟用": "active",
}

PLAN_MAP = {
    "FREE": "FREE",
    "PRO_199": "PRO_199",
    "PRO_PLUS_399": "PRO_PLUS_399",
    "ULTRA_1599": "ULTRA_1599",
}


@then('系統應建立新帳號，訂閱方案為 "{plan}"，狀態為 "{status}"')
def step_impl(context, plan, status):
    # 從 last_response 中取得新建帳號的 email
    response = context.last_response
    data = response.json()
    email = data.get("email") or data.get("user", {}).get("email")
    assert email is not None, f"回應中找不到 email 欄位: {data}"

    # 從 DB 查詢驗證
    repo = UserRepository(context.db_session)
    context.db_session.expire_all()
    user = repo.find_by_email(email)
    assert user is not None, f"DB 中找不到 email='{email}' 的使用者"

    expected_plan = PLAN_MAP.get(plan, plan)
    assert user.subscription_plan.value == expected_plan, \
        f"訂閱方案應為 '{expected_plan}'，實際為 '{user.subscription_plan.value}'"

    expected_status = STATUS_MAP.get(status, status)
    assert user.status.value == expected_status, \
        f"狀態應為 '{expected_status}'，實際為 '{user.status.value}'"
