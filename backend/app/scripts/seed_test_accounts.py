#!/usr/bin/env python3
"""Seed 完整權限矩陣測試帳號（CLI 版）。

對應 ``docs/permission-model.md`` 的「6. 測試帳號」段。每個權限層各建一名帳號，
密碼統一 ``test1234``，供端對端權限驗證使用（管理者 redirect、tier gate 顯示等）。

Idempotent：已存在的帳號會被更新為標準狀態（ACTIVE + 對應 role/plan + 重設密碼）。

使用方式::

    .venv/bin/python -m app.scripts.seed_test_accounts

亦可透過 HTTP 端點觸發（雲端用）::

    POST /api/v1/auth/seed-test-accounts
"""

import hashlib
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.user import User, UserStatus, UserRole, SubscriptionPlan

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PASSWORD = "test1234"

# (email, role, plan, display_name)
MATRIX = [
    ("super-admin@certimate.test", UserRole.SUPER_ADMIN, SubscriptionPlan.ULTRA, "Test Super Admin"),
    ("admin@certimate.test", UserRole.ADMIN, SubscriptionPlan.FREE, "Test Admin (FREE)"),
    ("ultra@certimate.test", UserRole.USER, SubscriptionPlan.ULTRA, "Test ULTRA User"),
    ("pro-plus@certimate.test", UserRole.USER, SubscriptionPlan.PRO_PLUS, "Test PRO_PLUS User"),
    ("pro@certimate.test", UserRole.USER, SubscriptionPlan.PRO, "Test PRO User"),
    ("free@certimate.test", UserRole.USER, SubscriptionPlan.FREE, "Test FREE User"),
    ("edu@certimate.test", UserRole.STUDENT, SubscriptionPlan.EDU, "Test EDU Student"),
]


def main() -> None:
    """建立 / 更新所有測試帳號。"""
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    pw_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()

    try:
        for email, role, plan, display_name in MATRIX:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                existing.role = role
                existing.subscription_plan = plan
                existing.status = UserStatus.ACTIVE
                existing.onboarding_completed = True
                existing.password_hash = pw_hash
                log.info("  ↻ 更新: %s (%s / %s)", email, role.value, plan.value)
            else:
                db.add(User(
                    email=email,
                    password_hash=pw_hash,
                    display_name=display_name,
                    role=role,
                    status=UserStatus.ACTIVE,
                    subscription_plan=plan,
                    onboarding_completed=True,
                ))
                log.info("  ✓ 新增: %s (%s / %s)", email, role.value, plan.value)
        db.commit()
        log.info("=" * 60)
        log.info("完成。密碼統一: %s", PASSWORD)
    finally:
        db.close()


if __name__ == "__main__":
    main()
