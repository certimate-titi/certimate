"""Auth API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleSSORequest,
    ForgotPasswordRequest,
    PasswordStrengthRequest,
)

router = APIRouter()


def _get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/auth/register")
def register(request: RegisterRequest, service: AuthService = Depends(_get_auth_service)):
    result = service.register(request.email, request.password, request.agreed_to_terms)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/auth/login")
def login(request: LoginRequest, service: AuthService = Depends(_get_auth_service)):
    result = service.login(request.email, request.password)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/auth/google-sso")
def google_sso(request: GoogleSSORequest, service: AuthService = Depends(_get_auth_service)):
    result = service.google_sso(request.email, request.google_token)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result


@router.post("/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest, service: AuthService = Depends(_get_auth_service)):
    result = service.forgot_password(request.email)
    return result


@router.post("/auth/password-strength")
def password_strength(request: PasswordStrengthRequest, service: AuthService = Depends(_get_auth_service)):
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


@router.delete("/auth/delete-account")
def delete_account(
    user_id: str = Depends(get_current_user_id),
    service: AuthService = Depends(_get_auth_service),
):
    result = service.delete_account(user_id)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result
