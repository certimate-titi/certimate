"""Then 使用者的訂閱方案應為 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User

# API display name → DB enum value
PLAN_DISPLAY_TO_DB = {
    "PRO_199": "PRO",
    "PRO_PLUS_399": "PRO_PLUS",
    "ULTRA_1599": "ULTRA",
}


@then('使用者 "{email}" 的訂閱方案應為 "{expected_plan}"')
def step_impl(context, email, expected_plan):
    db = context.db_session

    if email in context.ids:
        user_id = uuid.UUID(context.ids[email])
        user = db.query(User).filter_by(id=user_id).first()
    else:
        # Fallback: lookup by email directly (e.g., user created via CSV import)
        user = db.query(User).filter_by(email=email).first()

    assert user is not None, f"找不到使用者 {email}"
    db.refresh(user)
    actual = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    expected_db = PLAN_DISPLAY_TO_DB.get(expected_plan, expected_plan)
    assert actual == expected_db, \
        f"預期訂閱方案 '{expected_plan}'(DB: '{expected_db}')，實際 '{actual}'"
