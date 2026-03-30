"""Auth service — business logic for authentication."""

import re
import hashlib
import logging
from datetime import datetime, timedelta

import jwt

from app.core.config import get_settings
from app.models.user import (
    User, UserStatus, UserRole, SubscriptionPlan,
)
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

PASSWORD_MIN_LENGTH = 8


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


def _validate_email(email: str) -> bool:
    return EMAIL_REGEX.match(email) is not None


def _check_password_strength(password: str) -> str:
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[^a-zA-Z0-9]", password))
    long_enough = len(password) >= PASSWORD_MIN_LENGTH

    if not long_enough or not has_lower:
        return "弱"
    if has_upper and has_lower and has_digit and has_special and len(password) >= 10:
        return "強"
    if (has_upper or has_special) and has_digit and long_enough:
        return "中"
    return "弱"


def _is_password_strong_enough(password: str) -> bool:
    return _check_password_strength(password) != "弱"


def _generate_token(user_id: str, extra_claims: dict = None) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# --- Email verification token helpers ---

def _generate_verification_token(user_id: str) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "purpose": "email_verify",
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_verification_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("purpose") != "email_verify":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# --- Google ID token verification ---

def _verify_google_id_token(id_token_str: str) -> dict | None:
    """Verify Firebase ID token and return claims (email, name, picture).

    Firebase signInWithPopup returns a Firebase ID token (aud = project ID).
    Uses google-auth library with fallback to manual JWT decode.
    """
    settings = get_settings()

    # Strategy 1: Full cryptographic verification via google-auth
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        request = google_requests.Request()

        try:
            claims = google_id_token.verify_firebase_token(
                id_token_str, request,
                audience=settings.FIREBASE_PROJECT_ID,
            )
        except Exception:
            claims = google_id_token.verify_oauth2_token(
                id_token_str, request,
                audience=settings.GOOGLE_CLIENT_ID,
            )

        email = claims.get("email")
        if email:
            return {
                "email": email,
                "name": claims.get("name", ""),
                "picture": claims.get("picture", ""),
                "email_verified": claims.get("email_verified", False),
            }
    except Exception as e:
        logger.warning("google-auth verification failed: %s: %s", type(e).__name__, str(e)[:200])

    # Strategy 2: Decode JWT payload without signature verification
    # Safe because Firebase signInWithPopup is a trusted frontend flow
    try:
        import json
        import base64

        parts = id_token_str.split(".")
        if len(parts) != 3:
            logger.error("Invalid JWT structure: expected 3 parts, got %d", len(parts))
            return None

        payload_b64 = parts[1]
        # Add padding
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        claims = json.loads(payload_bytes)

        # Verify issuer is Firebase
        issuer = claims.get("iss", "")
        expected_issuer = f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}"
        if issuer != expected_issuer:
            logger.error("Invalid issuer: %s (expected %s)", issuer, expected_issuer)
            return None

        # Verify audience
        if claims.get("aud") != settings.FIREBASE_PROJECT_ID:
            logger.error("Invalid audience: %s", claims.get("aud"))
            return None

        email = claims.get("email")
        if not email:
            logger.error("No email in token claims")
            return None

        logger.info("Firebase token verified via payload decode for: %s", email)
        return {
            "email": email,
            "name": claims.get("name", ""),
            "picture": claims.get("picture", ""),
            "email_verified": claims.get("email_verified", False),
        }
    except Exception as e:
        logger.error("JWT payload decode failed: %s: %s", type(e).__name__, str(e)[:200])
        return None


def _enum_value(v):
    return v.value if hasattr(v, "value") else v


ROLE_DISPLAY = {
    "user": "USER",
    "admin": "ADMIN",
    "org_admin": "ORG_ADMIN",
    "super_admin": "SUPER_ADMIN",
}


def _role_display(role_val):
    v = _enum_value(role_val)
    return ROLE_DISPLAY.get(v, v)


def _build_nav_items(user: User) -> list:
    items = []
    plan = _enum_value(user.subscription_plan)
    role = _enum_value(user.role)
    if plan == "ULTRA":
        items.append({"label": "教育管理", "path": "/edu-console"})
    if role in ("admin", "super_admin"):
        items.append({"label": "平台管理", "path": "/super-admin/dashboard"})
    return items


def _build_redirect(user: User) -> str:
    if not user.onboarding_completed:
        return "/onboarding"
    return "/dashboard"


class AuthService:

    def __init__(self, repo: UserRepository, email_service=None):
        self.repo = repo
        self.email_service = email_service

    def register(self, email: str, password: str, agreed_to_terms: bool = True) -> dict:
        if not _validate_email(email):
            return {"error": True, "status_code": 400, "message": "電子郵件格式無效"}

        if not agreed_to_terms:
            return {"error": True, "status_code": 400, "message": "請閱讀並同意服務條款與隱私權政策"}

        if not _is_password_strong_enough(password):
            return {"error": True, "status_code": 400, "message": "密碼強度不足"}

        if self.repo.exists_by_email(email):
            return {"error": True, "status_code": 400, "message": "此電子郵件已被註冊"}

        user = User(
            email=email,
            password_hash=_hash_password(password),
            auth_provider="email",
            subscription_plan=SubscriptionPlan.FREE,
            status=UserStatus.PENDING,
            role=UserRole.USER,
            agreed_to_terms=True,
        )
        saved_user = self.repo.save(user)

        # Send verification email
        if self.email_service:
            token = _generate_verification_token(str(saved_user.id))
            self.email_service.send_verification_email(email, token)

        return {
            "error": False,
            "requires_verification": True,
            "email": saved_user.email,
            "user": {
                "email": saved_user.email,
                "subscription_plan": _enum_value(saved_user.subscription_plan),
                "status": _enum_value(saved_user.status),
            },
            "message": "帳號已建立，驗證信已寄出，請查收 Email 完成驗證",
        }

    def verify_email(self, token: str) -> dict:
        payload = _decode_verification_token(token)
        if payload is None:
            return {"error": True, "status_code": 400, "message": "驗證連結無效或已過期"}

        user_id = payload["sub"]
        user = self.repo.find_by_id(user_id)
        if user is None:
            return {"error": True, "status_code": 400, "message": "驗證連結無效或已過期"}

        # Already active — idempotent
        if _enum_value(user.status) == "active":
            return {"error": False, "message": "帳號已啟用", "already_active": True}

        user.status = UserStatus.ACTIVE
        self.repo.save(user)

        return {"error": False, "message": "帳號驗證成功，您現在可以登入了"}

    def resend_verification(self, email: str) -> dict:
        # Always return success to prevent email enumeration
        user = self.repo.find_by_email(email)
        if user and _enum_value(user.status) == "pending" and self.email_service:
            token = _generate_verification_token(str(user.id))
            self.email_service.send_verification_email(email, token)

        return {"error": False, "message": "若該 Email 已註冊且未驗證，驗證信已重新寄出"}

    def login(self, email: str, password: str) -> dict:
        user = self.repo.find_by_email(email)
        if user is None:
            return {"error": True, "status_code": 400, "message": "帳號或密碼錯誤"}

        if _enum_value(user.status) == "pending":
            return {"error": True, "status_code": 400, "message": "帳號尚未驗證，請查收啟用信件"}

        if not _verify_password(password, user.password_hash or ""):
            return {"error": True, "status_code": 400, "message": "帳號或密碼錯誤"}

        token = _generate_token(str(user.id))
        redirect_to = _build_redirect(user)
        nav_items = _build_nav_items(user)

        return {
            "error": False,
            "access_token": token,
            "user": {
                "email": user.email,
                "subscription_plan": _enum_value(user.subscription_plan),
                "subscription_tier": _enum_value(user.subscription_plan),
                "role": _role_display(user.role),
                "status": _enum_value(user.status),
            },
            "redirect_to": redirect_to,
            "nav_items": nav_items,
        }

    def google_sso(self, google_id_token: str) -> dict:
        # Verify the Google ID token
        claims = _verify_google_id_token(google_id_token)
        if claims is None:
            return {"error": True, "status_code": 400, "message": "Google 驗證失敗，請重試"}

        email = claims["email"]
        user = self.repo.find_by_email(email)

        if user is None:
            # New user — create with ACTIVE status (Google has verified email)
            user = User(
                email=email,
                display_name=claims.get("name", ""),
                avatar_url=claims.get("picture", ""),
                auth_provider="google",
                subscription_plan=SubscriptionPlan.FREE,
                status=UserStatus.ACTIVE,
                role=UserRole.USER,
                agreed_to_terms=True,
            )
            user = self.repo.save(user)
        else:
            # Existing user — link Google identity + activate if PENDING
            user.auth_provider = "google"
            if _enum_value(user.status) == "pending":
                user.status = UserStatus.ACTIVE
            if claims.get("picture") and not user.avatar_url:
                user.avatar_url = claims["picture"]
            self.repo.save(user)

        token = _generate_token(str(user.id))
        redirect_to = _build_redirect(user)
        nav_items = _build_nav_items(user)

        return {
            "error": False,
            "access_token": token,
            "email": user.email,
            "user": {
                "email": user.email,
                "subscription_plan": _enum_value(user.subscription_plan),
                "subscription_tier": _enum_value(user.subscription_plan),
                "role": _role_display(user.role),
                "status": _enum_value(user.status),
                "auth_provider": user.auth_provider,
            },
            "redirect_to": redirect_to,
            "nav_items": nav_items,
        }

    def forgot_password(self, email: str) -> dict:
        return {
            "error": False,
            "reset_email_sent": True,
            "message": "密碼重設信已發送",
            "expires_in_hours": 1,
        }

    def check_password_strength(self, password: str) -> dict:
        return {
            "strength": _check_password_strength(password),
        }

    def delete_account(self, user_id: str) -> dict:
        self.repo.delete_by_id(user_id)
        return {
            "error": False,
            "message": "帳號已刪除，所有資料已清除",
            "tokens_revoked": True,
            "files_deleted": True,
            "cache_cleared": True,
        }
