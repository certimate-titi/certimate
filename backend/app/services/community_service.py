"""Community Service — 社群歸屬與主動關懷。"""

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.exam import Exam
from app.models.weekly_report import WeeklyReport


class CommunityService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, user_id: str) -> dict:
        """Get dashboard with optional banner for ULTRA users."""
        user = self.db.query(User).filter_by(id=uuid.UUID(user_id)).first()
        if not user:
            return {"banner": None}

        plan = user.subscription_plan
        if hasattr(plan, "value"):
            plan = plan.value

        # Only ULTRA users see the banner
        if plan in ("ULTRA", "ULTRA_1599"):
            cutoff_date = date.today() - timedelta(days=7)
            active_count = self.db.query(User).filter(
                User.last_login_at.isnot(None),
                func.date(User.last_login_at) >= cutoff_date,
            ).count()
            return {
                "banner": {
                    "type": "study_buddy",
                    "message": f"目前有 {active_count} 位考生正一起奮鬥"
                }
            }
        return {"banner": None}

    def generate_weekly_reports(self, activities: dict) -> dict:
        """Generate weekly reports for users with activity."""
        reports = []
        for user_email, activity in activities.items():
            if activity is None:
                continue
            user = self.db.query(User).filter_by(email=user_email).first()
            if not user:
                continue
            report = WeeklyReport(
                user_id=user.id,
                report_week=date.today(),
                study_hours=activity["study_hours"],
                exams_completed=activity["exams_completed"],
                questions_answered=activity["questions_answered"],
                progress_summary="本週學習表現良好，持續保持！建議可以加強弱點領域的練習。",
            )
            self.db.add(report)
            reports.append({
                "user_email": user_email,
                "study_hours": float(activity["study_hours"]),
                "exams_completed": activity["exams_completed"],
                "questions_answered": activity["questions_answered"],
                "progress_summary": report.progress_summary,
            })
        self.db.commit()
        return {"reports": reports}

    def run_valley_detection(self, current_date_str: str) -> dict:
        """Detect inactive users and send recall notifications."""
        current = datetime.strptime(current_date_str, "%Y-%m-%d").date()
        threshold = current - timedelta(days=3)

        # Find users whose last login date is strictly before the threshold date
        inactive_users = self.db.query(User).filter(
            User.last_login_at.isnot(None),
            func.date(User.last_login_at) < threshold,
        ).all()

        notifications = []
        for user in inactive_users:
            display_name = user.display_name or user.email.split("@")[0]
            notifications.append({
                "email": user.email,
                "title": f"{display_name}，我們想你了！",
                "tone": "warm",
                "body": f"嗨 {display_name}，好久不見！學習的路上有我們陪你，回來看看最新的學習資源吧",
            })

        return {"notifications": notifications}

    def get_exam_coaching(self, user_id: str) -> dict:
        """Check if AI coach should proactively appear based on score trends."""
        exams = (
            self.db.query(Exam)
            .filter_by(user_id=uuid.UUID(user_id))
            .filter(Exam.score.isnot(None))
            .order_by(Exam.created_at.desc())
            .limit(3)
            .all()
        )

        if len(exams) < 2:
            return {"coaching_triggered": False}

        # Reverse to get chronological order
        scores = [e.score for e in reversed(exams)]
        decline_count = sum(1 for i in range(1, len(scores)) if scores[i] < scores[i - 1])

        if decline_count >= 2:
            return {
                "coaching_triggered": True,
                "coach_name": "Certi",
                "message": {
                    "情緒支持": "你最近很努力，成績的波動是學習過程中很正常的現象，不要氣餒！",
                    "策略建議": "建議可以回顧錯題本，針對薄弱的知識點進行重點複習，每天花 15 分鐘專注練習。",
                },
            }
        return {"coaching_triggered": False}
