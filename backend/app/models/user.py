"""User ORM Model — derived from erm.dbml users table."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    func,
)
from datetime import date as date_type
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class SubscriptionPlan(str, enum.Enum):
    """訂閱方案列舉（DB 值；API 顯示名另行映射）。"""

    FREE = "FREE"
    PRO = "PRO"
    PRO_PLUS = "PRO_PLUS"
    ULTRA = "ULTRA"
    EDU = "EDU"


class SubscriptionStatus(str, enum.Enum):
    """訂閱狀態列舉。"""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"


class UserStatus(str, enum.Enum):
    """使用者帳號狀態列舉。"""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COOLING = "cooling"
    DELETED = "deleted"


class UserRole(str, enum.Enum):
    """使用者角色列舉（user / student / org_admin / admin / super_admin）。"""

    USER = "user"
    STUDENT = "student"
    ORG_ADMIN = "org_admin"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class LearningPreference(str, enum.Enum):
    """學習偏好列舉（題海 / 概念 / 混合）。"""

    DRILL = "drill"
    CONCEPT = "concept"
    MIXED = "mixed"


class User(Base):
    """使用者主檔（B2C 散客 / B2B 學生 / 教師 / 管理員）。

    對應 DBML 表：users

    Attributes:
        email: 信箱（unique）
        display_name / avatar_url: 顯示名稱與頭像
        auth_provider: email / google / firebase
        password_hash: bcrypt 密碼雜湊（auth_provider=email 時）
        subscription_plan: FREE / PRO / PRO_PLUS / ULTRA / EDU
        subscription_status: active / cancelled / expired / trial
        plan_source: payment / admin（升級來源）
        trial_start_date / trial_end_date / has_used_trial / pre_trial_plan: 試用相關
        org_id: 所屬機構（B2B）
        role: USER / STUDENT / ORG_ADMIN / ADMIN / SUPER_ADMIN
        status: pending / active / suspended / cooling / deleted
        onboarding_completed: 是否完成新手導引
        daily_study_minutes / learning_preference: 學習偏好
        current_streak / longest_streak / freezes_remaining: 連續學習日相關
        last_active_date: 最後活躍日（streak 計算）
    """

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
    trial_start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    trial_end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    has_used_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    pre_trial_plan: Mapped[str | None] = mapped_column(String(20))
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True)
    )
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
    current_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    freezes_remaining: Mapped[int] = mapped_column(Integer, default=2, server_default="2")
    freezes_per_week: Mapped[int] = mapped_column(Integer, default=2, server_default="2")
    last_active_date: Mapped[date_type | None] = mapped_column(Date)
    freeze_consumed_today: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
