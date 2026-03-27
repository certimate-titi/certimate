"""異常維修管理 API。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.services.anomaly_service import AnomalyService

router = APIRouter(prefix="/admin")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


# ── Anomaly Tracking ──

@router.get("/anomalies")
def list_anomalies(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AnomalyService(db)
    result = service.list_anomalies(user_id=user_id)
    return _handle_result(result)


class UpdateAnomalyRequest(BaseModel):
    status: str
    assigned_to: Optional[str] = None


@router.put("/anomalies/{error_id}")
def update_anomaly(
    error_id: str,
    request: UpdateAnomalyRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AnomalyService(db)
    result = service.update_anomaly(
        user_id=user_id,
        error_id=error_id,
        status=request.status,
        assigned_to=request.assigned_to,
    )
    return _handle_result(result)


# ── Maintenance Tasks ──

class CreateMaintenanceTaskRequest(BaseModel):
    name: Optional[str] = None
    priority: Optional[str] = None
    related_error: Optional[str] = None
    estimated_hours: Optional[float] = None


@router.post("/maintenance-tasks")
def create_maintenance_task(
    request: CreateMaintenanceTaskRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AnomalyService(db)
    result = service.create_maintenance_task(user_id=user_id, data=request.model_dump())
    return _handle_result(result)


class UpdateTaskStatusRequest(BaseModel):
    status: str


@router.put("/maintenance-tasks/{task_id}/status")
def update_maintenance_task_status(
    task_id: str,
    request: UpdateTaskStatusRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AnomalyService(db)
    result = service.update_maintenance_task_status(user_id=user_id, task_id=task_id, status=request.status)
    return _handle_result(result)


# ── Maintenance Schedules ──

class CreateMaintenanceScheduleRequest(BaseModel):
    name: str
    starts_at: str
    ends_at: str
    notify_channels: Optional[str] = None
    notify_targets: Optional[str] = None
    notify_before: Optional[str] = None


@router.post("/maintenance-schedules")
def create_maintenance_schedule(
    request: CreateMaintenanceScheduleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AnomalyService(db)
    result = service.create_maintenance_schedule(user_id=user_id, data=request.model_dump())
    return _handle_result(result)


class ActivateMaintenanceModeRequest(BaseModel):
    reason: str
    estimated_recovery: str


@router.post("/maintenance-mode")
def activate_maintenance_mode(
    request: ActivateMaintenanceModeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = AnomalyService(db)
    result = service.activate_maintenance_mode(
        user_id=user_id,
        reason=request.reason,
        estimated_recovery=request.estimated_recovery,
    )
    return _handle_result(result)


@router.post("/maintenance-schedules/check-end")
def check_schedule_end(
    db: Session = Depends(get_db),
):
    service = AnomalyService(db)
    result = service.check_schedule_end()
    return _handle_result(result)
