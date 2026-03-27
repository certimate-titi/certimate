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


@router.delete("/auth/delete-account")
def delete_account(
    user_id: str = Depends(get_current_user_id),
    service: AuthService = Depends(_get_auth_service),
):
    result = service.delete_account(user_id)
    if result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])
    return result
