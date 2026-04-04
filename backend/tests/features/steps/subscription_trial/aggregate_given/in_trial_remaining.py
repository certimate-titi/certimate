"""Given — 使用者正在 ULTRA 試用中且有剩餘天數。"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.user import User, SubscriptionPlan, SubscriptionStatus


@given('使用者 "{email}" 正在 ULTRA 試用中，剩餘 {days:d} 天')
def step_in_trial_remaining(context, email, days):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    now = datetime.now(timezone.utc)

    user.subscription_plan = SubscriptionPlan.ULTRA
    user.subscription_status = SubscriptionStatus.TRIAL
    user.has_used_trial = True
    user.trial_start_date = now - timedelta(days=(14 - days))
    # Add a small buffer to avoid off-by-one from time elapsed between Given and When
    user.trial_end_date = now + timedelta(days=days, hours=1)
    user.pre_trial_plan = "FREE"
    db.commit()
