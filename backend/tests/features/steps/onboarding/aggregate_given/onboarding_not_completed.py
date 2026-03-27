"""Given 使用者尚未完成 Onboarding — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User


@given('使用者 "{email}" 尚未完成 Onboarding')
def step_impl(context, email):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    user.onboarding_completed = False
    db.commit()
