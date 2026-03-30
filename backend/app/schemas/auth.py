"""Auth Pydantic schemas."""

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    agreed_to_terms: bool = True


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleSSORequest(BaseModel):
    google_id_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class PasswordStrengthRequest(BaseModel):
    password: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: str
