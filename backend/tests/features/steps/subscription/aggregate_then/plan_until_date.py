"""Then — 驗證使用者在指定日期前方案維持不變。"""

import uuid

from behave import then

from app.models.user import User


@then('使用者 "{email}" 在 {date} 前的訂閱方案應維持 "{plan}"')
def step_plan_until_date(context, email, date, plan):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    db.refresh(user)
    actual = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

    # Map API plan names to DB plan names
    plan_mapping = {
        "PRO_199": "PRO",
        "PRO_PLUS_399": "PRO_PLUS",
        "ULTRA_1599": "ULTRA",
    }
    expected_db = plan_mapping.get(plan, plan)

    assert actual == expected_db or actual == plan, \
        f"預期 {date} 前方案維持 '{plan}'，實際 '{actual}'"
