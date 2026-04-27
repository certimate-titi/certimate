"""Feature 33 — 成本監控中心 API Router.

所有 endpoint 都在 require_super_admin dependency 之下，一般 admin 不可存取。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.permissions import AuditAction, require_super_admin
from app.models.audit_log import AdminAuditLog
from app.models.user import User
from app.services.budget_service import BudgetService
from app.services.cost_monitor_service import CostMonitorService

router = APIRouter(prefix="/admin/cost")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        detail: dict = {"message": result.get("message", "error")}
        if "code" in result:
            detail["code"] = result["code"]
        raise HTTPException(status_code=status_code, detail=detail)
    return result


def _record_view(db: Session, admin_id, endpoint: str) -> None:
    db.add(
        AdminAuditLog(
            admin_id=admin_id,
            action=AuditAction.COST_MONITOR_VIEWED,
            target_type="cost_monitor",
            details={"endpoint": endpoint},
        )
    )
    db.commit()


# ---------------------------------------------------------------------------
# Read endpoints
# ---------------------------------------------------------------------------


@router.get("/summary")
def get_cost_summary(
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """get cost summary。

    此 endpoint 對應 `get_cost_summary` 操作。

    Args:
        super_admin: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    _record_view(db, super_admin.id, "/admin/cost/summary")
    service = CostMonitorService(db)
    return _handle_result(service.get_summary())


@router.get("/providers/{provider}")
def get_provider_detail(
    provider: str,
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """get provider detail。

    此 endpoint 對應 `get_provider_detail` 操作。

    Args:
        provider: 參數。
        super_admin: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    _record_view(db, super_admin.id, f"/admin/cost/providers/{provider}")
    service = CostMonitorService(db)
    return _handle_result(service.get_provider_detail(provider))


@router.get("/gcp/services")
def get_gcp_services(
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """get gcp services。

    此 endpoint 對應 `get_gcp_services` 操作。

    Args:
        super_admin: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    _record_view(db, super_admin.id, "/admin/cost/gcp/services")
    service = CostMonitorService(db)
    return _handle_result(service.get_gcp_services())


@router.get("/trends")
def get_trends(
    days: int = 30,
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """get trends。

    此 endpoint 對應 `get_trends` 操作。

    Args:
        days: 參數。
        super_admin: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail={"message": "days 須介於 1-90"})
    _record_view(db, super_admin.id, "/admin/cost/trends")
    service = CostMonitorService(db)
    return _handle_result(service.get_trends(days=days))


# ---------------------------------------------------------------------------
# Budget CRUD
# ---------------------------------------------------------------------------


class UpdateBudgetRequest(BaseModel):
    scope: Literal["AI_ANTHROPIC", "AI_GEMINI", "AI_VOYAGE", "GCP_TOTAL"]
    monthly_limit_usd: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=2, max_length=500)


@router.put("/budget")
def update_budget(
    payload: UpdateBudgetRequest,
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """update budget。

    此 endpoint 對應 `update_budget` 操作。

    Args:
        payload: 參數。
        super_admin: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = BudgetService(db)
    result = service.update_budget(
        super_admin=super_admin,
        scope=payload.scope,
        new_limit_usd=payload.monthly_limit_usd,
        reason=payload.reason,
    )
    return _handle_result(result)


class GlobalScaleRequest(BaseModel):
    scale_factor: Decimal | None = None
    target_total_usd: Decimal | None = None
    reason: str = Field(..., min_length=2, max_length=500)


@router.post("/budget/global-scale")
def global_scale_budgets(
    payload: GlobalScaleRequest,
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """global scale budgets。

    此 endpoint 對應 `global_scale_budgets` 操作。

    Args:
        payload: 參數。
        super_admin: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    if payload.scale_factor is None and payload.target_total_usd is None:
        raise HTTPException(
            status_code=400,
            detail={"message": "必須提供 scale_factor 或 target_total_usd"},
        )
    service = BudgetService(db)
    result = service.global_scale(
        super_admin=super_admin,
        scale_factor=payload.scale_factor,
        target_total_usd=payload.target_total_usd,
        reason=payload.reason,
    )
    return _handle_result(result)


class OverrideDisableRequest(BaseModel):
    scope: Literal["AI_ANTHROPIC", "AI_GEMINI", "AI_VOYAGE", "GCP_TOTAL"]
    reason: str = Field(..., min_length=2, max_length=500)


@router.post("/budget/override-disable")
def override_disable(
    payload: OverrideDisableRequest,
    super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """override disable。

    此 endpoint 對應 `override_disable` 操作。

    Args:
        payload: 參數。
        super_admin: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = BudgetService(db)
    result = service.override_disable(
        super_admin=super_admin,
        scope=payload.scope,
        reason=payload.reason,
    )
    return _handle_result(result)
