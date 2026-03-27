"""Given 使用者正在進行 Onboarding 流程 — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User


@given('使用者 "{email}" 正在進行 Onboarding 流程')
def step_impl(context, email):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    user.onboarding_completed = False
    db.commit()

    # Store JWT token for subsequent When steps
    token = context.jwt_helper.generate_token(context.ids[email])
    context.memo["current_token"] = token
    context.memo["current_email"] = email
