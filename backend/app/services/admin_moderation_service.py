"""Admin Moderation Service — AI abuse monitoring and content report handling."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ai_cooldown import AiCooldown
from app.models.audit_log import AdminAuditLog
from app.models.content_report import ContentReport, ReportStatus
from app.models.resource import Resource, ResourceStatus
from app.models.user import User, UserRole, UserStatus


class AdminModerationService:
    def __init__(self, db: Session):
        self.db = db

    def _is_admin(self, user_id: str) -> bool:
        user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return False
        role = user.role.value if hasattr(user.role, "value") else str(user.role)
        return role in ("admin", "super_admin")

    # ── AI Abuse Monitoring ─────────────────────────────────────────────────

    def get_ai_abuse_dashboard(self, actor_id: str) -> dict:
        if not self._is_admin(actor_id):
            return {"error": True, "status_code": 403, "message": "權限不足"}

        now = datetime.now(timezone.utc)
        cooldowns = self.db.query(AiCooldown).all()

        cooling_users = []
        for cd in cooldowns:
            user = self.db.query(User).filter(User.id == cd.user_id).first()
            if not user:
                continue
            remaining_seconds = max(0, int((cd.cooldown_until - now).total_seconds()))
            cooling_users.append({
                "user_id": str(cd.user_id),
                "email": user.email,
                "reason": cd.reason,
                "cooldown_until": cd.cooldown_until.isoformat(),
                "remaining_seconds": remaining_seconds,
            })

        return {"cooling_users": cooling_users}

    def unlock_cooldown(self, actor_id: str, target_user_id: str) -> dict:
        if not self._is_admin(actor_id):
            return {"error": True, "status_code": 403, "message": "權限不足"}

        target_uuid = uuid.UUID(target_user_id)

        # Remove all cooldown records for this user
        self.db.query(AiCooldown).filter(AiCooldown.user_id == target_uuid).delete()

        # Update user status from COOLING to ACTIVE
        user = self.db.query(User).filter(User.id == target_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        status_val = user.status.value if hasattr(user.status, "value") else str(user.status)
        if status_val == "cooling":
            user.status = UserStatus.ACTIVE

        # Record audit log
        audit_log = AdminAuditLog(
            admin_id=uuid.UUID(actor_id),
            action="unlock_cooldown",
            target_type="user",
            target_id=target_uuid,
            details={"target_user_id": target_user_id},
        )
        self.db.add(audit_log)
        self.db.commit()

        return {"message": "冷卻已解除"}

    # ── Content Report Queue ────────────────────────────────────────────────

    def get_report_queue(self, actor_id: str, status: str | None = None) -> dict:
        if not self._is_admin(actor_id):
            return {"error": True, "status_code": 403, "message": "權限不足"}

        query = self.db.query(ContentReport)
        if status:
            query = query.filter(ContentReport.status == status)

        reports = query.all()
        result = []
        for r in reports:
            result.append({
                "id": str(r.id),
                "report_ref": r.report_ref,
                "reporter_id": r.reporter_id,
                "report_type": r.report_type,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "status": r.status,
                "resolution_action": r.resolution_action,
                "resolution_note": r.resolution_note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        return {"reports": result}

    def resolve_report(
        self,
        actor_id: str,
        report_ref: str,
        action: str,
        note: str,
    ) -> dict:
        if not self._is_admin(actor_id):
            return {"error": True, "status_code": 403, "message": "權限不足"}

        report = self.db.query(ContentReport).filter(
            ContentReport.report_ref == report_ref
        ).first()
        if not report:
            return {"error": True, "status_code": 404, "message": "檢舉不存在"}

        if action == "delete_and_warn":
            report.status = ReportStatus.RESOLVED
        elif action == "dismiss":
            report.status = ReportStatus.DISMISSED
        else:
            return {"error": True, "status_code": 400, "message": f"未知動作: {action}"}

        report.resolution_action = action
        report.resolution_note = note
        report.resolved_by = actor_id

        # Soft-delete the target resource when action is "delete_and_warn"
        if action == "delete_and_warn" and report.target_type == "resource":
            try:
                target_uuid = uuid.UUID(report.target_id)
                resource = self.db.query(Resource).filter(
                    Resource.id == target_uuid
                ).first()
                if resource:
                    resource.status = ResourceStatus.DELETED
            except (ValueError, AttributeError):
                pass  # target_id is not a valid UUID; skip resource deletion

        # Record audit log
        audit_log = AdminAuditLog(
            admin_id=uuid.UUID(actor_id),
            action="resolve_report",
            target_type="content_report",
            details={
                "report_ref": report_ref,
                "action": action,
                "note": note,
            },
        )
        self.db.add(audit_log)
        self.db.commit()

        return {"message": "檢舉已處理", "status": report.status}
