"""Pricing API — 定價比較頁與升級引導。"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing")


def _get_optional_user_id(request: Request) -> str | None:
    """Extract user_id from JWT if present, None otherwise."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        from app.core.config import get_settings
        import jwt
        s = get_settings()
        payload = jwt.decode(token, s.JWT_SECRET_KEY, algorithms=[s.JWT_ALGORITHM])
        return payload.get("sub") or payload.get("user_id")
    except Exception:
        return None


@router.get("")
def get_pricing(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = _get_optional_user_id(request)
    service = PricingService(db)
    return service.get_pricing(user_id=user_id)


@router.post("/check-upload")
def check_upload_limit(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = PricingService(db)
    result = service.check_upload_limit(user_id=user_id)
    if result.get("error"):
        status_code = result.pop("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result)
    return result


@router.post("/check-ai-chat")
def check_ai_chat_limit(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = PricingService(db)
    result = service.check_ai_chat_limit(user_id=user_id)
    if result.get("error"):
        status_code = result.pop("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result)
    return result
