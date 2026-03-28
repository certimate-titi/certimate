"""Seed demo users for local development."""

import hashlib
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.user import User, UserStatus, UserRole, SubscriptionPlan
from app.models.plan_quota import PlanQuota
from app.models.ai_model_routing import AiModelRouting
from app.models.feature_flag import FeatureFlag


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


DEMO_USERS = [
    {
        "email": "user1@test.com",
        "display_name": "User1 新用戶",
        "password": "123",
        "subscription_plan": SubscriptionPlan.FREE,
        "role": UserRole.USER,
        "onboarding_completed": False,
    },
    {
        "email": "user2@test.com",
        "display_name": "User2 PRO",
        "password": "123",
        "subscription_plan": SubscriptionPlan.PRO,
        "role": UserRole.USER,
        "onboarding_completed": True,
    },
    {
        "email": "proplus@test.com",
        "display_name": "ProPlus User",
        "password": "123",
        "subscription_plan": SubscriptionPlan.PRO_PLUS,
        "role": UserRole.USER,
        "onboarding_completed": True,
    },
    {
        "email": "ultra@test.com",
        "display_name": "Ultra 教育管理員",
        "password": "123",
        "subscription_plan": SubscriptionPlan.ULTRA,
        "role": UserRole.USER,
        "onboarding_completed": True,
    },
    {
        "email": "admin@test.com",
        "display_name": "平台管理者",
        "password": "123",
        "subscription_plan": SubscriptionPlan.FREE,
        "role": UserRole.ADMIN,
        "onboarding_completed": True,
    },
    {
        "email": "admin@certimate.com",
        "display_name": "Super Admin",
        "password": "admin123",
        "subscription_plan": SubscriptionPlan.FREE,
        "role": UserRole.SUPER_ADMIN,
        "onboarding_completed": True,
    },
]


def seed():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        for user_data in DEMO_USERS:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                print(f"  [skip] {user_data['email']} already exists")
                continue

            user = User(
                email=user_data["email"],
                display_name=user_data["display_name"],
                password_hash=_hash_password(user_data["password"]),
                auth_provider="email",
                subscription_plan=user_data["subscription_plan"],
                role=user_data["role"],
                status=UserStatus.ACTIVE,
                onboarding_completed=user_data["onboarding_completed"],
                agreed_to_terms=True,
            )
            db.add(user)
            print(f"  [created] {user_data['email']} ({user_data['role'].value}, {user_data['subscription_plan'].value})")

        db.commit()
        print("\n✅ Demo users seeded successfully!")

        # ── Plan Quotas (from 12c feature file) ──
        print("\n🌱 Seeding plan quotas...")
        PLAN_QUOTAS = [
            {"plan": "FREE", "monthly_uploads": 5, "monthly_exams": 10, "daily_ai_chats": 3, "monthly_vision_pages": 0, "max_file_size_mb": 10},
            {"plan": "PRO", "monthly_uploads": 50, "monthly_exams": 100, "daily_ai_chats": 30, "monthly_vision_pages": 0, "max_file_size_mb": 50},
            {"plan": "PRO_PLUS", "monthly_uploads": 100, "monthly_exams": 200, "daily_ai_chats": 60, "monthly_vision_pages": 50, "max_file_size_mb": 100},
            {"plan": "ULTRA", "monthly_uploads": 999, "monthly_exams": 999, "daily_ai_chats": 999, "monthly_vision_pages": 200, "max_file_size_mb": 200},
        ]
        for pq in PLAN_QUOTAS:
            existing = db.query(PlanQuota).filter(PlanQuota.plan == pq["plan"]).first()
            if existing:
                print(f"  [skip] PlanQuota {pq['plan']} already exists")
                continue
            db.add(PlanQuota(**pq))
            print(f"  [created] PlanQuota {pq['plan']}")
        db.commit()
        print("✅ Plan quotas seeded!")

        # ── AI Model Routing (from 12c feature file) ──
        print("\n🌱 Seeding AI model routing...")
        MODEL_ROUTINGS = [
            {"plan": "FREE", "task_type": "basic", "primary_model": "gemini-1.5-flash", "fallback_model": "llama-3.1-8b"},
            {"plan": "PRO", "task_type": "advanced", "primary_model": "claude-3.5-sonnet", "fallback_model": "gemini-1.5-flash"},
        ]
        for mr in MODEL_ROUTINGS:
            existing = db.query(AiModelRouting).filter(
                AiModelRouting.plan == mr["plan"], AiModelRouting.task_type == mr["task_type"]
            ).first()
            if existing:
                print(f"  [skip] Routing {mr['plan']}/{mr['task_type']} already exists")
                continue
            db.add(AiModelRouting(**mr))
            print(f"  [created] Routing {mr['plan']}/{mr['task_type']}: {mr['primary_model']}")
        db.commit()
        print("✅ AI model routing seeded!")

        # ── Feature Flags (from 12c feature file) ──
        print("\n🌱 Seeding feature flags...")
        FEATURE_FLAGS = [
            {"flag_key": "enable_socratic_tutor_v2", "enabled": False, "rollout_percentage": 0},
        ]
        for ff in FEATURE_FLAGS:
            existing = db.query(FeatureFlag).filter(FeatureFlag.flag_key == ff["flag_key"]).first()
            if existing:
                print(f"  [skip] FeatureFlag {ff['flag_key']} already exists")
                continue
            db.add(FeatureFlag(**ff))
            print(f"  [created] FeatureFlag {ff['flag_key']}")
        db.commit()
        print("✅ Feature flags seeded!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    print("🌱 Seeding demo users...")
    seed()
