"""Users API — 使用者公開操作 (頭像等)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id

router = APIRouter(prefix="/users")


@router.post("/avatar")
def upload_avatar(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """上傳使用者頭像（JSON 模式）。"""
    from app.models.user import User
    user_uuid = uuid.UUID(user_id)
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    avatar_url = f"/avatars/{user_id}/avatar.jpg"
    user.avatar_url = avatar_url
    db.commit()

    return {
        "ok": True,
        "message": "頭像已更新",
        "avatar_url": avatar_url,
        "url": avatar_url,
    }
