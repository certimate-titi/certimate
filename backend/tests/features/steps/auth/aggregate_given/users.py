from datetime import datetime, timezone

from behave import given
from app.models.user import User, UserStatus, UserRole, SubscriptionPlan, SubscriptionStatus
from app.repositories.user_repository import UserRepository
from app.services.auth_service import _hash_password


STATUS_MAP = {
    "已啟用": UserStatus.ACTIVE,
    "待驗證": UserStatus.PENDING,
    "已停用": UserStatus.SUSPENDED,
    "冷卻中": UserStatus.COOLING,
    "已刪除": UserStatus.DELETED,
    # English values used in feature files
    "active": UserStatus.ACTIVE,
    "pending": UserStatus.PENDING,
    "suspended": UserStatus.SUSPENDED,
    "cooling": UserStatus.COOLING,
    "deleted": UserStatus.DELETED,
}

ROLE_MAP = {
    "USER": UserRole.USER,
    "ADMIN": UserRole.ADMIN,
    "ORG_ADMIN": UserRole.ORG_ADMIN,
    "SUPER_ADMIN": UserRole.SUPER_ADMIN,
    # Lowercase values used in feature files
    "user": UserRole.USER,
    "admin": UserRole.ADMIN,
    "org_admin": UserRole.ORG_ADMIN,
    "super_admin": UserRole.SUPER_ADMIN,
    # Chinese display labels
    "一般使用者": UserRole.USER,
    "平台管理員": UserRole.ADMIN,
    "機構管理員": UserRole.ORG_ADMIN,
    "超級管理員": UserRole.SUPER_ADMIN,
}

PLAN_MAP = {
    "FREE": SubscriptionPlan.FREE,
    "PRO": SubscriptionPlan.PRO,
    "PRO_199": SubscriptionPlan.PRO,
    "PRO_PLUS": SubscriptionPlan.PRO_PLUS,
    "PRO_PLUS_399": SubscriptionPlan.PRO_PLUS,
    "ULTRA": SubscriptionPlan.ULTRA,
    "ULTRA_1599": SubscriptionPlan.ULTRA,
}

SUB_STATUS_MAP = {
    "active": SubscriptionStatus.ACTIVE,
    "cancelled": SubscriptionStatus.CANCELLED,
    "expired": SubscriptionStatus.EXPIRED,
}

AUTH_PROVIDER_MAP = {
    "email": "email",
    "google": "google",
}


def _get_col(row, name, default=None):
    try:
        return row[name]
    except KeyError:
        return default


@given('系統中有以下使用者帳號：')
def step_impl(context):
    repo = UserRepository(context.db_session)

    for row in context.table:
        auth_provider_raw = _get_col(row, "驗證方式", "email")
        role_raw = _get_col(row, "角色", "USER")
        status_raw = _get_col(row, "狀態", "已啟用")

        # Optional subscription fields
        sub_status_raw = _get_col(row, "訂閱狀態", "active")
        billing_raw = _get_col(row, "下次扣款日", "null")
        next_billing = None
        if billing_raw and billing_raw not in ("null", ""):
            next_billing = datetime.fromisoformat(billing_raw).replace(tzinfo=timezone.utc)

        onboarding_raw = _get_col(row, "已完成 Onboarding") or _get_col(row, "Onboarding", "false")
        onboarding_completed = onboarding_raw.lower() in ("true", "1", "yes", "是")

        # Optional last login date
        last_login_raw = _get_col(row, "最後登入日")
        last_login_at = None
        if last_login_raw and last_login_raw not in ("null", ""):
            last_login_at = datetime.fromisoformat(last_login_raw).replace(tzinfo=timezone.utc)

        # Optional display name
        display_name_raw = _get_col(row, "顯示名稱")

        user = User(
            email=row["Email"],
            auth_provider=AUTH_PROVIDER_MAP.get(auth_provider_raw, auth_provider_raw),
            subscription_plan=PLAN_MAP.get(row["訂閱方案"], SubscriptionPlan.FREE),
            subscription_status=SUB_STATUS_MAP.get(sub_status_raw, SubscriptionStatus.ACTIVE),
            next_billing_date=next_billing,
            role=ROLE_MAP.get(role_raw, UserRole.USER),
            status=STATUS_MAP.get(status_raw, UserStatus.ACTIVE),
            password_hash=_hash_password("Password1!"),
            agreed_to_terms=True,
            onboarding_completed=onboarding_completed,
            last_login_at=last_login_at,
            display_name=display_name_raw,
        )
        saved_user = repo.save(user)
        context.ids[row["Email"]] = str(saved_user.id)
        user_id_col = _get_col(row, "使用者 ID")
        if user_id_col:
            context.ids[user_id_col] = str(saved_user.id)
            context.memo[f"user_{user_id_col}_plan"] = row["訂閱方案"]
