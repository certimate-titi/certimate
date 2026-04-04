"""Given — 使用者的 ULTRA 試用將於指定日期到期。"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.user import User, SubscriptionPlan, SubscriptionStatus


@given('使用者 "{email}" 的 ULTRA 試用將於 {date} 到期')
def step_trial_expiring(context, email, date):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    user.subscription_plan = SubscriptionPlan.ULTRA
    user.subscription_status = SubscriptionStatus.TRIAL
    user.has_used_trial = True

    trial_end = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    user.trial_end_date = trial_end
    user.trial_start_date = trial_end - timedelta(days=14)
    db.commit()
