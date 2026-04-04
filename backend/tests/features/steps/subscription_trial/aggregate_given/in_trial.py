"""Given — 使用者正在 ULTRA 試用中。"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.user import User, SubscriptionPlan, SubscriptionStatus


@given('使用者 "{email}" 正在 ULTRA 試用中')
def step_in_trial(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    user.subscription_plan = SubscriptionPlan.ULTRA
    user.subscription_status = SubscriptionStatus.TRIAL
    user.has_used_trial = True
    user.trial_start_date = datetime.now(timezone.utc)
    user.trial_end_date = datetime.now(timezone.utc) + timedelta(days=14)
    user.pre_trial_plan = user.subscription_plan.value if user.pre_trial_plan is None else user.pre_trial_plan
    db.commit()
