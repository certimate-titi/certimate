"""Auth Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: str
    password: str
    agreed_to_terms: bool = True


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleSSORequest(BaseModel):
    email: str
    google_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class PasswordStrengthRequest(BaseModel):
    password: str
