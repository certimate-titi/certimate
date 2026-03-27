"""Given 管理員登入系統 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.user import User, UserRole, UserStatus, SubscriptionPlan, SubscriptionStatus
from app.repositories.user_repository import UserRepository
from app.services.auth_service import _hash_password


@given('管理員登入系統')
def step_impl(context):
    db = context.db_session

    admin_email = "admin@certimate.com"

    # Check if admin already exists
    if admin_email not in context.ids:
        repo = UserRepository(db)
        admin = User(
            email=admin_email,
            auth_provider="email",
            subscription_plan=SubscriptionPlan.ULTRA,
            subscription_status=SubscriptionStatus.ACTIVE,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            password_hash=_hash_password("Admin1!"),
            agreed_to_terms=True,
        )
        saved = repo.save(admin)
        context.ids[admin_email] = str(saved.id)

    admin_id = context.ids[admin_email]
    token = context.jwt_helper.generate_token(admin_id)
    context.memo["admin_token"] = token
    context.memo["admin_email"] = admin_email
    context.memo["admin_id"] = admin_id
