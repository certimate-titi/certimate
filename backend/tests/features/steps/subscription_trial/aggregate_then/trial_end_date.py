"""Then — 驗證試用到期日為啟用日起第 N 天。"""

import uuid
from datetime import timedelta

from behave import then

from app.models.user import User


@then('使用者 "{email}" 的試用到期日應為啟用日起第 {days:d} 天')
def step_trial_end_date(context, email, days):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    db.refresh(user)

    assert user.trial_start_date is not None, "trial_start_date 為 None"
    assert user.trial_end_date is not None, "trial_end_date 為 None"

    expected_end = user.trial_start_date + timedelta(days=days)
    diff = abs((user.trial_end_date - expected_end).total_seconds())
    assert diff < 60, \
        f"試用到期日預期為啟用日起第 {days} 天 ({expected_end})，實際 {user.trial_end_date}"
