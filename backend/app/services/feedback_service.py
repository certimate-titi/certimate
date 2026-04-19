"""意見反饋 Service。"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from app.models.feedback import Feedback, FeedbackAttachment
from app.models.audit_log import AdminAuditLog


class FeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def submit_feedback(
        self,
        user_id: str,
        feedback_type: str,
        subject: str,
        content: str,
        attachments: list[dict] | None = None,
    ) -> dict:
        """提交意見反饋。"""
        user_uuid = uuid.UUID(user_id)

        # 驗證必要欄位
        if not feedback_type:
            return {"error": True, "status_code": 400, "message": "必要欄位未填寫"}
        if not subject:
            return {"error": True, "status_code": 400, "message": "必要欄位未填寫"}
        if not content:
            return {"error": True, "status_code": 400, "message": "必要欄位未填寫"}

        # 驗證長度
        if len(subject) > 100:
            return {"error": True, "status_code": 400, "message": "主旨不得超過 100 個字元"}
        if len(content) > 2000:
            return {"error": True, "status_code": 400, "message": "內容不得超過 2000 個字元"}

        # 驗證附件
        if attachments:
            if len(attachments) > 3:
                return {"error": True, "status_code": 400, "message": "最多只能上傳 3 張截圖"}
            for att in attachments:
                if att.get("file_size", 0) > 5 * 1024 * 1024:
                    return {"error": True, "status_code": 400, "message": "附件大小不得超過 5 MB"}

        # 1 小時內不可重複提交相同主旨
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        existing = (
            self.db.query(Feedback)
            .filter(
                Feedback.user_id == user_uuid,
                Feedback.subject == subject,
                Feedback.created_at >= one_hour_ago,
            )
            .first()
        )
        if existing:
            return {
                "error": True,
                "status_code": 400,
                "message": "您已於近期提交過相同主題的反饋，請稍後再試",
            }

        # 生成 feedback_id
        count = self.db.query(Feedback).count()
        fb_id = f"FB-{count + 1:03d}"

        fb = Feedback(
            feedback_id=fb_id,
            user_id=user_uuid,
            type=feedback_type,
            subject=subject,
            content=content,
            status="PENDING",
        )
        self.db.add(fb)
        self.db.flush()

        # 處理附件
        attachment_paths = []
        if attachments:
            for att in attachments:
                fa = FeedbackAttachment(
                    feedback_id=fb.id,
                    file_path=att["file_path"],
                    file_size=att.get("file_size", 0),
                    mime_type=att.get("mime_type", "image/png"),
                )
                self.db.add(fa)
                attachment_paths.append(fa.file_path)

        self.db.commit()

        # Email notification to admin
        try:
            from app.services.email_service import EmailService
            from app.models.user import User
            user = self.db.query(User).filter_by(id=user_uuid).first()
            user_email = user.email if user else "unknown"
            email_svc = EmailService()
            html = (
                f'<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">'
                f'<h2 style="color:#10b981">CertiMate — 新用戶反饋</h2>'
                f'<table style="width:100%;border-collapse:collapse;margin:16px 0">'
                f'<tr><td style="padding:8px;border-bottom:1px solid #e5e7eb;font-weight:bold">編號</td><td style="padding:8px;border-bottom:1px solid #e5e7eb">{fb_id}</td></tr>'
                f'<tr><td style="padding:8px;border-bottom:1px solid #e5e7eb;font-weight:bold">類型</td><td style="padding:8px;border-bottom:1px solid #e5e7eb">{feedback_type}</td></tr>'
                f'<tr><td style="padding:8px;border-bottom:1px solid #e5e7eb;font-weight:bold">主旨</td><td style="padding:8px;border-bottom:1px solid #e5e7eb">{subject}</td></tr>'
                f'<tr><td style="padding:8px;border-bottom:1px solid #e5e7eb;font-weight:bold">提交者</td><td style="padding:8px;border-bottom:1px solid #e5e7eb">{user_email}</td></tr>'
                f'<tr><td style="padding:8px;font-weight:bold">附件</td><td style="padding:8px">{len(attachment_paths)} 張</td></tr>'
                f'</table>'
                f'<div style="background:#f8fafc;padding:16px;border-radius:8px;margin:16px 0">'
                f'<p style="white-space:pre-wrap;margin:0">{content}</p></div>'
                f'<a href="https://certimate-titi.web.app/super-admin/moderation" '
                f'style="display:inline-block;padding:10px 24px;background:#10b981;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;margin-top:16px">'
                f'前往管理後台處理</a></div>'
            )
            email_svc._send(
                to_email="certimate.web@gmail.com",
                subject=f"[CertiMate 反饋] {feedback_type} — {subject}",
                html_body=html,
            )
        except Exception as e:
            logger.warning("Feedback email notification failed: %s", e)

        return {
            "feedback_id": fb_id,
            "status": "PENDING",
            "attachments": attachment_paths,
        }

    def list_user_feedbacks(self, user_id: str) -> dict:
        """列出使用者自己的反饋清單。"""
        user_uuid = uuid.UUID(user_id)
        feedbacks = (
            self.db.query(Feedback)
            .filter_by(user_id=user_uuid)
            .order_by(Feedback.created_at.desc())
            .all()
        )
        items = []
        for fb in feedbacks:
            items.append({
                "feedback_id": fb.feedback_id,
                "type": fb.type,
                "subject": fb.subject,
                "content": fb.content or "",
                "status": fb.status,
                "admin_reply": fb.admin_reply or "",
                "resolved_at": fb.resolved_at.isoformat() if fb.resolved_at else None,
                "created_at": fb.created_at.isoformat() if fb.created_at else None,
            })
        return {"feedbacks": items, "count": len(items)}

    def get_feedback_detail(self, user_id: str, feedback_id: str) -> dict:
        """取得單筆反饋詳情。"""
        user_uuid = uuid.UUID(user_id)
        fb = self.db.query(Feedback).filter_by(
            feedback_id=feedback_id, user_id=user_uuid
        ).first()
        if not fb:
            return {"error": True, "status_code": 404, "message": "找不到反饋紀錄"}

        return {
            "feedback_id": fb.feedback_id,
            "type": fb.type,
            "subject": fb.subject,
            "content": fb.content,
            "status": fb.status,
            "admin_reply": fb.admin_reply or "",
            "resolved_at": fb.resolved_at.isoformat() if fb.resolved_at else None,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }

    def admin_list_feedbacks(self, status_filter: str | None = None) -> dict:
        """管理員查看所有反饋。"""
        from app.models.user import User

        query = self.db.query(Feedback, User.email).outerjoin(
            User, Feedback.user_id == User.id
        )
        if status_filter:
            query = query.filter(Feedback.status == status_filter)
        rows = query.order_by(Feedback.created_at.desc()).all()
        items = []
        for fb, user_email in rows:
            content_preview = fb.content[:100] + "..." if fb.content and len(fb.content) > 100 else (fb.content or "")
            # Fetch attachment URLs
            att_rows = self.db.query(FeedbackAttachment).filter_by(feedback_id=fb.id).all()
            attachment_urls = [a.file_path for a in att_rows]
            items.append({
                "feedback_id": fb.feedback_id,
                "type": fb.type,
                "subject": fb.subject,
                "content_preview": content_preview,
                "content": fb.content or "",
                "status": fb.status,
                "user_id": str(fb.user_id),
                "user_email": user_email or "unknown",
                "admin_reply": fb.admin_reply or "",
                "attachment_urls": attachment_urls,
                "created_at": fb.created_at.isoformat() if fb.created_at else None,
                "resolved_at": fb.resolved_at.isoformat() if fb.resolved_at else None,
            })
        return {"feedbacks": items, "count": len(items)}

    def admin_update_feedback(
        self,
        admin_id: str,
        feedback_id: str,
        new_status: str,
        admin_reply: str | None = None,
        close_reason: str | None = None,
    ) -> dict:
        """管理員更新反饋狀態。"""
        admin_uuid = uuid.UUID(admin_id)
        fb = self.db.query(Feedback).filter_by(feedback_id=feedback_id).first()
        if not fb:
            return {"error": True, "status_code": 404, "message": "找不到反饋紀錄"}

        old_status = fb.status
        fb.status = new_status

        if admin_reply:
            fb.admin_reply = admin_reply
        if close_reason:
            fb.close_reason = close_reason
        if new_status == "RESOLVED":
            fb.resolved_at = datetime.now(timezone.utc)

        # 記錄審計日誌
        details_text = f"{old_status} → {new_status}"
        if admin_reply:
            from app.models.user import User
            admin = self.db.query(User).filter_by(id=admin_uuid).first()
            admin_email = admin.email if admin else str(admin_uuid)
            details_text += f"，{admin_email} 回覆"

        audit = AdminAuditLog(
            admin_id=admin_uuid,
            action="update_feedback_status",
            target_type="feedback",
            details={
                "target": feedback_id,
                "details": details_text,
            },
        )
        self.db.add(audit)
        self.db.commit()

        # Send email notification to user when admin replies
        if admin_reply:
            try:
                from app.services.email_service import EmailService
                from app.models.user import User
                user = self.db.query(User).filter_by(id=fb.user_id).first()
                if user and user.email:
                    email_svc = EmailService()
                    status_label = {"PENDING": "待處理", "REVIEWING": "處理中", "RESOLVED": "已解決"}.get(new_status, new_status)
                    html = (
                        f'<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">'
                        f'<h2 style="color:#10b981">CertiMate — 您的反饋已收到回覆</h2>'
                        f'<table style="width:100%;border-collapse:collapse;margin:16px 0">'
                        f'<tr><td style="padding:8px;border-bottom:1px solid #e5e7eb;font-weight:bold">編號</td><td style="padding:8px;border-bottom:1px solid #e5e7eb">{feedback_id}</td></tr>'
                        f'<tr><td style="padding:8px;border-bottom:1px solid #e5e7eb;font-weight:bold">主旨</td><td style="padding:8px;border-bottom:1px solid #e5e7eb">{fb.subject}</td></tr>'
                        f'<tr><td style="padding:8px;font-weight:bold">狀態</td><td style="padding:8px">{status_label}</td></tr>'
                        f'</table>'
                        f'<div style="background:#f0fdf4;padding:16px;border-radius:8px;margin:16px 0;border:1px solid #bbf7d0">'
                        f'<p style="font-weight:bold;color:#15803d;margin:0 0 8px 0">管理員回覆：</p>'
                        f'<p style="white-space:pre-wrap;margin:0;color:#334155">{admin_reply}</p></div>'
                        f'<a href="https://certimate-titi.web.app/feedback" '
                        f'style="display:inline-block;padding:10px 24px;background:#10b981;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;margin-top:16px">'
                        f'查看我的反饋</a></div>'
                    )
                    email_svc._send(
                        to_email=user.email,
                        subject=f"[CertiMate] 您的反饋 {feedback_id} 已收到回覆",
                        html_body=html,
                    )
            except Exception as e:
                logger.warning("Feedback reply email failed: %s", e)

        return {
            "feedback_id": fb.feedback_id,
            "status": fb.status,
            "resolved_at": fb.resolved_at.isoformat() if fb.resolved_at else None,
        }

    def admin_get_stats(self) -> dict:
        """管理員查看反饋統計。"""
        total = self.db.query(Feedback).count()
        pending = self.db.query(Feedback).filter_by(status="PENDING").count()
        reviewing = self.db.query(Feedback).filter_by(status="REVIEWING").count()
        resolved = self.db.query(Feedback).filter_by(status="RESOLVED").count()

        # 最多反饋的類型
        top_type_row = (
            self.db.query(Feedback.type, sa_func.count(Feedback.id).label("cnt"))
            .group_by(Feedback.type)
            .order_by(sa_func.count(Feedback.id).desc())
            .first()
        )
        top_category = top_type_row[0] if top_type_row else None

        # 平均解決時間
        resolved_fbs = (
            self.db.query(Feedback)
            .filter(Feedback.status == "RESOLVED", Feedback.resolved_at.isnot(None))
            .all()
        )
        if resolved_fbs:
            total_hours = sum(
                (fb.resolved_at - fb.created_at).total_seconds() / 3600
                for fb in resolved_fbs
                if fb.resolved_at and fb.created_at
            )
            avg_hours = round(total_hours / len(resolved_fbs), 1)
        else:
            avg_hours = 0

        return {
            "total_count": total,
            "pending_count": pending,
            "reviewing_count": reviewing,
            "resolved_count": resolved,
            "top_category": top_category,
            "avg_resolve_hours": avg_hours,
        }
