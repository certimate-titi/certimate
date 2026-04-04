"""放榜通知 Service。"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject


class ResultNotificationService:
    def __init__(self, db: Session):
        self.db = db

    def send_result_day_notifications(self):
        """放榜日當天發送考試結果確認通知。"""
        today = date.today()

        journeys = (
            self.db.query(LearningJourney)
            .filter(
                LearningJourney.result_date == today,
                LearningJourney.exam_result_status.is_(None),
            )
            .all()
        )

        notifications = []
        for j in journeys:
            from app.models.user import User
            user = self.db.query(User).filter_by(id=j.user_id).first()
            if user:
                notifications.append({
                    "email": user.email,
                    "user_email": user.email,
                    "type": "result_confirm",
                    "content": "請確認您是否考取",
                    "actions": [
                        {"label": "確認考取", "action": "passed"},
                        {"label": "未考取", "action": "failed"},
                    ],
                })

        # Top-level also includes actions for single-notification convenience
        actions = notifications[0]["actions"] if notifications else []
        return {
            "notifications": notifications,
            "count": len(notifications),
            "content": "請確認您是否考取" if notifications else "",
            "actions": actions,
        }

    def send_reminder(self):
        """放榜日+3 天未回覆發送提醒。"""
        cutoff = date.today() - timedelta(days=3)

        journeys = (
            self.db.query(LearningJourney)
            .filter(
                LearningJourney.result_date <= cutoff,
                LearningJourney.exam_result_status.is_(None),
            )
            .all()
        )

        sent = len(journeys)
        return {
            "reminder_sent": sent > 0,
            "type": "reminder",
            "count": sent,
        }

    def process_default(self):
        """放榜日+7 天未回覆預設為未考取。"""
        cutoff = date.today() - timedelta(days=7)

        journeys = (
            self.db.query(LearningJourney)
            .filter(
                LearningJourney.result_date <= cutoff,
                LearningJourney.exam_result_status.is_(None),
            )
            .all()
        )

        for j in journeys:
            j.exam_result_status = "failed"
            j.data_expiry_date = date.today() + timedelta(days=30)

        self.db.commit()

        return {
            "processed_count": len(journeys),
            "default_status": "failed",
            "retention_days": 30,
            "message": "資料將保留 30 天",
        }

    def cross_recommend(self):
        """交叉推薦相關證照。"""
        journeys = (
            self.db.query(LearningJourney)
            .filter(LearningJourney.exam_result_status == "passed")
            .all()
        )

        recommendations = []
        for j in journeys:
            subject = self.db.query(Subject).filter_by(id=j.subject_id).first()
            if subject:
                # 推薦同分類的其他科目
                related = (
                    self.db.query(Subject)
                    .filter(
                        Subject.category_id == subject.category_id,
                        Subject.id != subject.id,
                    )
                    .limit(3)
                    .all()
                )
                if related:
                    recommendations.extend([
                        {"id": str(s.id), "name": s.name}
                        for s in related
                    ])

        return {
            "notification_type": "cross_recommend",
            "type": "recommend",
            "recommendations": recommendations,
            "subjects": recommendations,
        }
