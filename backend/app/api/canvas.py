"""Knowledge Canvas API — PRD-046 三層 Zoom 視覺化。

Endpoints:
- GET /api/v1/subjects/{subject_id}/canvas — Tier 1 領域層
- GET /api/v1/subjects/{subject_id}/canvas/children/{parent_id} — Tier 2/3
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id, get_db_with_tenant
from app.services.canvas_service import CanvasService

router = APIRouter(prefix="/subjects", tags=["canvas"])


def _handle(result: dict) -> dict:
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result.get("message", "錯誤")},
        )
    return result


@router.get("/{subject_id}/canvas")
def get_canvas_tier1(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """取得領域層（depth=0）節點，每個節點含子樹聚合掌握度。"""
    return _handle(CanvasService(db).get_tier1(subject_id, user_id))


@router.get("/{subject_id}/canvas/children/{parent_id}")
def get_canvas_children(
    subject_id: str,
    parent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_with_tenant),
):
    """取得指定 parent 下的子節點（Tier 2/3）。"""
    return _handle(CanvasService(db).get_children(subject_id, parent_id, user_id))
