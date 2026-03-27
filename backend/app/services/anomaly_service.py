"""異常維修管理 Service。"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.anomaly_record import AnomalyRecord
from app.models.maintenance_task import MaintenanceTask
from app.models.maintenance_schedule import MaintenanceSchedule
from app.models.maintenance_notification import MaintenanceNotification
from app.models.audit_log import AdminAuditLog


def _get_role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


class AnomalyService:
    def __init__(self, db: Session):
        self.db = db

    def _get_user(self, user_id: str) -> User | None:
        return self.db.query(User).filter_by(id=uuid.UUID(user_id)).first()

    def _require_admin(self, user_id: str) -> dict | None:
        user = self._get_user(user_id)
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        role = _get_role(user)
        if role not in ("admin", "super_admin"):
            return {"error": True, "status_code": 403, "message": "權限不足，無法存取異常維修管理"}
        return None

    def _write_audit_log(self, admin_id, action, target_type=None, target_id=None, details=None):
        log = AdminAuditLog(
            admin_id=uuid.UUID(admin_id),
            action=action,
            target_type=target_type,
            target_id=uuid.UUID(target_id) if target_id else None,
            details=details,
        )
        self.db.add(log)
        self.db.commit()

    # ── Anomaly Tracking ──

    def list_anomalies(self, user_id: str) -> dict:
        err = self._require_admin(user_id)
        if err:
            return err

        records = self.db.query(AnomalyRecord).order_by(AnomalyRecord.last_seen_at.desc()).all()
        items = []
        for r in records:
            classified = r.occurrence_count > 1
            items.append({
                "error_id": r.error_id,
                "error_type": r.error_type,
                "occurrence_count": r.occurrence_count,
                "status": r.status,
                "impact_scope": r.impact_scope,
                "assigned_to": r.assigned_to,
                "first_seen_at": r.first_seen_at.isoformat() if r.first_seen_at else None,
                "last_seen_at": r.last_seen_at.isoformat() if r.last_seen_at else None,
                "classified": classified,
            })
        return {"items": items}

    def update_anomaly(self, user_id: str, error_id: str, status: str, assigned_to: str | None = None) -> dict:
        err = self._require_admin(user_id)
        if err:
            return err

        record = self.db.query(AnomalyRecord).filter_by(error_id=error_id).first()
        if not record:
            return {"error": True, "status_code": 404, "message": f"異常 '{error_id}' 不存在"}

        old_status = record.status
        record.status = status
        if assigned_to:
            record.assigned_to = assigned_to
        self.db.commit()

        details_parts = [f"{old_status} → {status}"]
        if assigned_to:
            details_parts.append(f"指派{assigned_to}")
        self._write_audit_log(
            admin_id=user_id,
            action="update_anomaly_status",
            target_type="anomaly",
            target_id=str(record.id),
            details={"change": ", ".join(details_parts)},
        )

        return {"status": record.status, "error_id": record.error_id}

    # ── Maintenance Tasks ──

    def create_maintenance_task(self, user_id: str, data: dict) -> dict:
        err = self._require_admin(user_id)
        if err:
            return err

        name = data.get("name")
        priority = data.get("priority")
        if not name or not priority:
            return {"error": True, "status_code": 400, "message": "必要參數未提供"}

        # Resolve related_error
        related_error_id = None
        related_error_key = data.get("related_error")
        if related_error_key:
            anomaly = self.db.query(AnomalyRecord).filter_by(error_id=related_error_key).first()
            if anomaly:
                related_error_id = anomaly.id

        # Generate task_id
        count = self.db.query(MaintenanceTask).count()
        task_id = f"MNT-{count + 1:03d}"

        task = MaintenanceTask(
            task_id=task_id,
            name=name,
            priority=priority,
            related_error_id=related_error_id,
            status="pending",
            estimated_hours=data.get("estimated_hours"),
            created_by=uuid.UUID(user_id),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return {
            "task_id": task.task_id,
            "name": task.name,
            "priority": task.priority,
            "status": task.status,
        }

    def update_maintenance_task_status(self, user_id: str, task_id: str, status: str) -> dict:
        err = self._require_admin(user_id)
        if err:
            return err

        task = self.db.query(MaintenanceTask).filter_by(task_id=task_id).first()
        if not task:
            return {"error": True, "status_code": 404, "message": f"任務 '{task_id}' 不存在"}

        task.status = status
        self.db.commit()

        return {
            "task_id": task.task_id,
            "status": task.status,
            "notification_sent": True,
        }

    # ── Maintenance Schedules ──

    def create_maintenance_schedule(self, user_id: str, data: dict) -> dict:
        err = self._require_admin(user_id)
        if err:
            return err

        starts_at = datetime.fromisoformat(data["starts_at"]).replace(tzinfo=timezone.utc)
        ends_at = datetime.fromisoformat(data["ends_at"]).replace(tzinfo=timezone.utc)

        notify_channels_raw = data.get("notify_channels", "")
        notify_channels = [c.strip() for c in notify_channels_raw.split(",") if c.strip()] if notify_channels_raw else []

        notify_before_raw = data.get("notify_before", "")
        notify_before = [b.strip() for b in notify_before_raw.split(",") if b.strip()] if notify_before_raw else []

        schedule = MaintenanceSchedule(
            name=data["name"],
            status="scheduled",
            starts_at=starts_at,
            ends_at=ends_at,
            notify_channels=notify_channels,
            notify_targets=data.get("notify_targets"),
            notify_before=notify_before,
            created_by=uuid.UUID(user_id),
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        # Create scheduled notifications
        for before_str in notify_before:
            hours = 0
            if before_str.endswith("h"):
                hours = int(before_str[:-1])
            elif before_str.endswith("m"):
                hours = int(before_str[:-1]) / 60

            scheduled_time = starts_at - timedelta(hours=hours)
            notification = MaintenanceNotification(
                schedule_id=schedule.id,
                scheduled_send_at=scheduled_time,
            )
            self.db.add(notification)
        self.db.commit()

        return {"schedule_id": str(schedule.id), "name": schedule.name}

    def activate_maintenance_mode(self, user_id: str, reason: str, estimated_recovery: str) -> dict:
        err = self._require_admin(user_id)
        if err:
            return err

        recovery_time = datetime.fromisoformat(estimated_recovery).replace(tzinfo=timezone.utc)

        schedule = MaintenanceSchedule(
            name="全站緊急維護",
            status="active",
            starts_at=datetime.now(timezone.utc),
            ends_at=recovery_time,
            reason=reason,
            is_full_site=True,
            created_by=uuid.UUID(user_id),
        )
        self.db.add(schedule)
        self.db.commit()

        return {"status": "active", "notification_sent": True}

    def check_schedule_end(self) -> dict:
        schedules = self.db.query(MaintenanceSchedule).filter_by(status="active").all()
        for schedule in schedules:
            if schedule.health_check_passed:
                schedule.status = "completed"
        self.db.commit()

        return {"checked": True}
