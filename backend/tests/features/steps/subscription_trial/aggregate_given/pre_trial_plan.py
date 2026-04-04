"""Given — 使用者試用前的方案。"""

import uuid

from behave import given

from app.models.user import User


@given('使用者 "{email}" 試用前的方案為 "{plan}"')
def step_pre_trial_plan(context, email, plan):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    user.pre_trial_plan = plan
    db.commit()
