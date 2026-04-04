"""Given 機構 N 目前已有 M 名 EDU 學生 — Aggregate Given"""

import hashlib
import uuid

from behave import given, use_step_matcher

from app.models.user import User, SubscriptionPlan, UserRole, UserStatus

use_step_matcher("re")


@given(r'機構 (?P<inst_id>\d+) 目前已有 (?P<count>\d+) 名 EDU 學生')
def step_impl(context, inst_id, count):
    db = context.db_session
    inst_uuid = uuid.UUID(int=int(inst_id))

    for i in range(int(count)):
        email = f"edu_student_{i+1}@seed.test"
        pw_hash = hashlib.sha256(f"{email}:certimate2026".encode()).hexdigest()
        user = User(
            email=email,
            display_name=f"EDU Student {i+1}",
            password_hash=pw_hash,
            subscription_plan=SubscriptionPlan.EDU,
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            org_id=inst_uuid,
        )
        db.add(user)

    db.flush()
    db.commit()


use_step_matcher("parse")
