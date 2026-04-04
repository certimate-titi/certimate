"""Then — 驗證試用剩餘天數。"""

from behave import then


@then('使用者 "{email}" 的試用剩餘天數應為 {days:d} 天')
def step_check_remaining_days(context, email, days):
    from datetime import datetime, timezone
    from app.models.user import User
    user = context.db_session.query(User).filter_by(email=email).first()
    assert user is not None, f"User {email} not found"
    assert user.trial_end_date is not None
    remaining = (user.trial_end_date - datetime.now(timezone.utc)).days
    assert remaining == days, f"Expected {days} days, got {remaining}"
