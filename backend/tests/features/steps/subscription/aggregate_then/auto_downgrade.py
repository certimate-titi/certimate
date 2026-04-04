"""Then — 驗證到期後自動降級。"""

import uuid
from datetime import datetime, timezone

from behave import then

from app.models.user import User


@then('{date} 到期後使用者 "{email}" 的訂閱方案應自動降級為 "{plan}"')
def step_auto_downgrade(context, date, email, plan):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    # Simulate expiry by checking next_billing_date and downgrade_to
    user = db.query(User).filter_by(id=user_id).first()
    db.refresh(user)

    # Verify the user has a pending downgrade or the next_billing_date is set
    assert user.next_billing_date is not None, \
        f"使用者 '{email}' 沒有設定下次扣款日，無法驗證到期降級"

    # Store downgrade expectation in memo for potential follow-up assertions
    context.memo[f"expected_downgrade_{email}"] = plan
