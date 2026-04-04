"""Given — 使用者已使用過 ULTRA 免費試用。"""

import uuid

from behave import given

from app.models.user import User


@given('使用者 "{email}" 已使用過 ULTRA 免費試用')
def step_has_used_trial(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    user.has_used_trial = True
    db.commit()
