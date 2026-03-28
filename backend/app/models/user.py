"""User ORM Model — derived from erm.dbml users table."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class SubscriptionPlan(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    PRO_PLUS = "PRO_PLUS"
    ULTRA = "ULTRA"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class UserStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COOLING = "cooling"
    DELETED = "deleted"


class UserRole(str, enum.Enum):
    USER = "user"
    ORG_ADMIN = "org_admin"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class LearningPreference(str, enum.Enum):
    DRILL = "drill"
    CONCEPT = "concept"
    MIXED = "mixed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    auth_provider: Mapped[str] = mapped_column(
        String(20), default="email"
    )
    password_hash: Mapped[str | None] = mapped_column(Text)
    subscription_plan: Mapped[str] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=SubscriptionPlan.FREE,
    )
    subscription_status: Mapped[str] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=SubscriptionStatus.ACTIVE,
    )
    next_billing_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    plan_source: Mapped[str | None] = mapped_column(String(20))  # 'payment' or 'admin'
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(
        Enum(UserRole, name="user_role", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=UserRole.USER,
    )
    status: Mapped[str] = mapped_column(
        Enum(UserStatus, name="user_status", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=UserStatus.ACTIVE,
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    daily_study_minutes: Mapped[int] = mapped_column(
        Integer, default=30
    )
    learning_preference: Mapped[str] = mapped_column(
        Enum(LearningPreference, name="learning_preference", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=LearningPreference.MIXED,
    )
    age: Mapped[int | None] = mapped_column(Integer)
    education: Mapped[str | None] = mapped_column(String(100))
    career: Mapped[str | None] = mapped_column(String(100))
    agreed_to_terms: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
