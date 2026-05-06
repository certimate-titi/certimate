"""Auth API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleSSORequest,
    ForgotPasswordRequest,
    PasswordStrengthRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
)

router = APIRouter()


def _get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db), email_service=EmailService())


@router.post("/auth/register")
def register(request: RegisterRequest, service: AuthService = Depends(_get_auth_service)):
    """register。

    此 endpoint 對應 `register` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    result = service.register(request.email, request.password, request.agreed_to_terms)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/auth/verify-email")
def verify_email(request: VerifyEmailRequest, service: AuthService = Depends(_get_auth_service)):
    """verify email。

    此 endpoint 對應 `verify_email` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    result = service.verify_email(request.token)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/auth/resend-verification")
def resend_verification(request: ResendVerificationRequest, service: AuthService = Depends(_get_auth_service)):
    """resend verification。

    此 endpoint 對應 `resend_verification` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    result = service.resend_verification(request.email)
    return result


@router.post("/auth/login")
def login(request: LoginRequest, service: AuthService = Depends(_get_auth_service)):
    """login。

    此 endpoint 對應 `login` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    result = service.login(request.email, request.password)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/auth/google-sso")
def google_sso(request: GoogleSSORequest, service: AuthService = Depends(_get_auth_service)):
    """google sso。

    此 endpoint 對應 `google_sso` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    result = service.google_sso(request.google_id_token, email_hint=request.email)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest, service: AuthService = Depends(_get_auth_service)):
    """forgot password。

    此 endpoint 對應 `forgot_password` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    result = service.forgot_password(request.email)
    return result


@router.post("/auth/reset-password")
def reset_password(request: ResetPasswordRequest, service: AuthService = Depends(_get_auth_service)):
    """reset password。

    此 endpoint 對應 `reset_password` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    result = service.reset_password(request.token, request.password)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/auth/password-strength")
def password_strength(request: PasswordStrengthRequest, service: AuthService = Depends(_get_auth_service)):
    """password strength。

    此 endpoint 對應 `password_strength` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    return service.check_password_strength(request.password)


@router.get("/auth/me")
def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得當前登入使用者的完整資料。"""
    repo = UserRepository(db)
    user = repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="使用者不存在")

    from app.services.auth_service import _enum_value, _role_display, _build_nav_items

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name or "",
        "avatar_url": user.avatar_url or "",
        "subscription_plan": _enum_value(user.subscription_plan),
        "subscription_tier": _enum_value(user.subscription_plan),
        "role": _role_display(user.role),
        "status": _enum_value(user.status),
        "onboarding_completed": user.onboarding_completed or False,
        "age": user.age,
        "education": user.education,
        "occupation": user.career,
        "daily_study_minutes": user.daily_study_minutes or 30,
        "learning_style": _enum_value(user.learning_preference),
        "nav_items": _build_nav_items(user),
    }


@router.post("/auth/refresh")
def refresh_token(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """以現有有效 JWT 換發新 JWT（重設 8 小時 TTL）。

    用途：前端在 token 快過期前靜默呼叫，避免長時間考試中斷。
    安全原則：
    - 必須帶有效 token（過期則無法 refresh，須重登）
    - 不重設 user 狀態檢查（user.status != active 仍拒絕）
    - 不引入 refresh token 概念，沿用單 token 滑動續期
    """
    repo = UserRepository(db)
    user = repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})
    if hasattr(user.status, 'value') and user.status.value != "active":
        raise HTTPException(status_code=403, detail={"message": "帳號狀態異常，無法續期"})

    from app.services.auth_service import _generate_token
    new_token = _generate_token(str(user.id))
    return {"access_token": new_token, "token_type": "bearer"}


@router.post("/auth/seed-demo")
def seed_demo_account(db: Session = Depends(get_db)):
    """建立 demo 帳號（已驗證 + SUPER_ADMIN），供 smoke test 與開發快速登入使用。"""
    from app.models.user import User, UserStatus, UserRole, SubscriptionPlan
    import hashlib

    repo = UserRepository(db)
    email = "admin@certimate.com"
    existing = repo.find_by_email(email)
    if existing:
        # Ensure existing account is active + admin
        if existing.status != UserStatus.ACTIVE or existing.role != UserRole.SUPER_ADMIN:
            existing.status = UserStatus.ACTIVE
            existing.role = UserRole.SUPER_ADMIN
            existing.subscription_plan = SubscriptionPlan.ULTRA
            existing.onboarding_completed = True
            existing.password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            db.commit()
            return {"message": "Demo account updated to active admin", "email": email}
        return {"message": "Demo account already exists", "email": email}

    user = User(
        email=email,
        password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
        display_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        subscription_plan=SubscriptionPlan.ULTRA,
        onboarding_completed=True,
    )
    db.add(user)
    db.commit()
    return {"message": "Demo account created", "email": email}


@router.post("/auth/seed-test-accounts")
def seed_test_accounts(db: Session = Depends(get_db)):
    """建立完整權限矩陣測試帳號（idempotent；每個權限層各 1）。

    對應 docs/permission-model.md 的「6. 測試帳號」段。供端對端權限驗證使用。
    密碼統一為 `test1234`。
    """
    from app.models.user import User, UserStatus, UserRole, SubscriptionPlan
    import hashlib

    repo = UserRepository(db)
    pw_hash = hashlib.sha256("test1234".encode()).hexdigest()

    # (email, role, plan, display_name)
    matrix = [
        ("super-admin@certimate.test", UserRole.SUPER_ADMIN, SubscriptionPlan.ULTRA, "Test Super Admin"),
        ("admin@certimate.test", UserRole.ADMIN, SubscriptionPlan.FREE, "Test Admin (FREE)"),
        ("ultra@certimate.test", UserRole.USER, SubscriptionPlan.ULTRA, "Test ULTRA User"),
        ("pro-plus@certimate.test", UserRole.USER, SubscriptionPlan.PRO_PLUS, "Test PRO_PLUS User"),
        ("pro@certimate.test", UserRole.USER, SubscriptionPlan.PRO, "Test PRO User"),
        ("free@certimate.test", UserRole.USER, SubscriptionPlan.FREE, "Test FREE User"),
        ("edu@certimate.test", UserRole.STUDENT, SubscriptionPlan.EDU, "Test EDU Student"),
    ]

    results = []
    for email, role, plan, display_name in matrix:
        existing = repo.find_by_email(email)
        if existing:
            existing.role = role
            existing.subscription_plan = plan
            existing.status = UserStatus.ACTIVE
            existing.onboarding_completed = True
            existing.password_hash = pw_hash
            results.append({"email": email, "action": "updated", "role": role.value, "plan": plan.value})
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
            results.append({"email": email, "action": "created", "role": role.value, "plan": plan.value})
    db.commit()
    return {"password": "test1234", "accounts": results}


@router.delete("/auth/delete-account")
def delete_account(
    user_id: str = Depends(get_current_user_id),
    service: AuthService = Depends(_get_auth_service),
):
    """delete account。

    此 endpoint 對應 `delete_account` 操作。

    Args:
        service: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    result = service.delete_account(user_id)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result
