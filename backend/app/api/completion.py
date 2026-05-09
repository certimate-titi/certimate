"""Completion API — 科目完成度框架。

GET /api/v1/subjects/{subject_id}/completion

依 orphan-mitigation-design.md B.2/B.3/B.4 計算三種加權進度、
徽章里程碑、邊際效益遞減 nudge。

回傳格式：
    {
        "subject_id": str,
        "sweet_spot_progress": int,       # 0-100
        "full_coverage_progress": int,
        "sprint_mode_progress": int,
        "badges_unlocked": list[str],
        "next_milestone": {"code": str, "remaining_pct": float} | null,
        "should_show_marginal_utility_nudge": bool,
        "computed_at": str                # ISO datetime
    }
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.completion_service import CompletionService

router = APIRouter(prefix="/subjects")


def _handle(result: dict):
    """將 service error dict 轉換為 HTTPException。"""
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


@router.get("/{subject_id}/completion")
def get_subject_completion(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """查詢指定科目的完成度框架資料。

    - sweet_spot_progress：高頻考點加權進度（主要顯示）
    - full_coverage_progress：全節點覆蓋進度
    - sprint_mode_progress：前 30% 高頻節點衝刺進度
    - badges_unlocked：已解鎖的徽章清單
    - next_milestone：下一個未解鎖里程碑及距離百分比
    - should_show_marginal_utility_nudge：是否顯示策略轉換建議

    Raises:
        HTTPException 401: JWT 未帶或無效
        HTTPException 404: 科目不存在
    """
    service = CompletionService(db)
    result = service.compute(user_id=user_id, subject_id=subject_id)
    return _handle(result)
