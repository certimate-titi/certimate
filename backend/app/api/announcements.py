"""公開公告 API — 一般用戶可讀取生效中的系統公告。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.services.admin_settings_service import AdminSettingsService

router = APIRouter(prefix="/announcements")


@router.get("")
def get_active_announcements(db: Session = Depends(get_db)):
    """取得目前生效中的公告（不需認證）。"""
    service = AdminSettingsService(db)
    return service.get_active_announcements()
