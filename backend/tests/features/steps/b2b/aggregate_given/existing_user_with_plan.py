"""Given 系統中已存在使用者，訂閱方案為 — Aggregate Given"""

from behave import given

from app.models.user import User, SubscriptionPlan, UserRole, UserStatus


PLAN_MAP = {
    "FREE": SubscriptionPlan.FREE,
    "PRO": SubscriptionPlan.PRO,
    "PRO_199": SubscriptionPlan.PRO,
    "PRO_PLUS": SubscriptionPlan.PRO_PLUS,
    "PRO_PLUS_399": SubscriptionPlan.PRO_PLUS,
    "ULTRA": SubscriptionPlan.ULTRA,
    "ULTRA_1599": SubscriptionPlan.ULTRA,
    "EDU": SubscriptionPlan.EDU,
}


@given('系統中已存在使用者 "{email}"，訂閱方案為 "{plan}"')
def step_impl(context, email, plan):
    db = context.db_session

    user = db.query(User).filter_by(email=email).first()
    if user:
        user.subscription_plan = PLAN_MAP.get(plan, SubscriptionPlan.FREE)
    else:
        user = User(
            email=email,
            display_name=email.split("@")[0],
            password_hash="test_hash",
            subscription_plan=PLAN_MAP.get(plan, SubscriptionPlan.FREE),
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
    db.commit()
