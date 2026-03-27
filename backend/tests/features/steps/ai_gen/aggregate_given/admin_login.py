"""Given 管理員登入系統 — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User, UserRole, UserStatus, SubscriptionPlan
from app.repositories.user_repository import UserRepository
from app.services.auth_service import _hash_password


@given('管理員登入系統')
def step_impl(context):
    db = context.db_session
    repo = UserRepository(db)

    admin_email = "admin@certimate.com"

    # Check if admin already exists
    existing = repo.find_by_email(admin_email)
    if not existing:
        admin = User(
            email=admin_email,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            subscription_plan=SubscriptionPlan.ULTRA,
            password_hash=_hash_password("AdminPass1!"),
            agreed_to_terms=True,
        )
        saved = repo.save(admin)
        context.ids[admin_email] = str(saved.id)
    else:
        existing.role = UserRole.ADMIN
        db.commit()
        context.ids[admin_email] = str(existing.id)

    context.memo["admin_email"] = admin_email
    context.memo["admin_token"] = context.jwt_helper.generate_token(
        context.ids[admin_email]
    )
