"""Then — 驗證系統不應在原試用到期日觸發降級。"""

import uuid

from behave import then

from app.models.user import User, SubscriptionStatus


@then('系統不應在原試用到期日觸發降級')
def step_no_downgrade_trigger(context):
    db = context.db_session

    # Find the user from the last response or previous context
    # The user who converted to paid should still be ULTRA with active status
    # Look for users with ULTRA plan and active status
    users = db.query(User).filter_by(
        subscription_status=SubscriptionStatus.ACTIVE,
    ).all()

    # At least one user should have active ULTRA (the converted one)
    ultra_active = [u for u in users if u.subscription_plan.value == "ULTRA"]
    assert len(ultra_active) > 0, \
        "預期至少有一個 ULTRA active 用戶（已轉正式訂閱），但找不到"
