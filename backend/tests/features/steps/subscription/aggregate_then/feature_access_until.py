"""Then — 驗證使用者在到期前仍可使用高階教練功能。"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 "{email}" 在 {date} 前仍可使用高階教練功能')
def step_feature_access_until(context, email, date):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    db.refresh(user)
    plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

    # PRO_PLUS and ULTRA have advanced coach access
    plans_with_coach = {"PRO_PLUS", "PRO_PLUS_399", "ULTRA", "ULTRA_1599"}
    assert plan in plans_with_coach, \
        f"預期使用者在 {date} 前仍有高階教練權限，但方案為 '{plan}'"
