"""Given 機構有 N 名 EDU 學生 — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User, SubscriptionPlan, SubscriptionStatus, UserRole
from app.repositories.user_repository import UserRepository
from app.services.auth_service import _hash_password


@given('機構 {inst_id:d} 有 {count:d} 名 EDU 學生')
def step_impl(context, inst_id, count):
    db = context.db_session
    inst_uuid = uuid.UUID(int=inst_id)
    repo = UserRepository(db)

    # Create EDU student users for this institution
    for i in range(count):
        email = f"edu_student_{inst_id}_{i + 1}@example.com"
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            existing.subscription_plan = SubscriptionPlan.EDU
            existing.subscription_status = SubscriptionStatus.ACTIVE
            existing.role = UserRole.STUDENT
            existing.org_id = inst_uuid
        else:
            student = User(
                email=email,
                auth_provider="email",
                subscription_plan=SubscriptionPlan.EDU,
                subscription_status=SubscriptionStatus.ACTIVE,
                role=UserRole.STUDENT,
                org_id=inst_uuid,
                password_hash=_hash_password("Password1!"),
                agreed_to_terms=True,
            )
            saved = repo.save(student)
            context.ids[email] = str(saved.id)

    db.commit()
    context.memo[f"institution_{inst_id}_edu_count"] = count
