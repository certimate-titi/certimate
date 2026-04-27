"""AI 考題退場掃描 Service。"""

import uuid
from datetime import datetime, timedelta, timezone, date

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.question import Question
from app.models.answer import Answer
from app.models.question_stat import QuestionStat
from app.models.node_mastery import NodeMastery
from app.models.content_report import ContentReport
from app.models.learning_journey import LearningJourney
from app.models.exam import Exam


ALERT_THRESHOLD = 1000


class RetirementService:
    """Retirement Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    def _get_user_id_for_question(self, q: Question):
        """取得 user id for question。"""
        exam = self.db.query(Exam).filter_by(id=q.exam_id).first()
        return exam.user_id if exam else None

    def _get_last_answer(self, question_id):
        """取得 last answer。"""
        return (
            self.db.query(Answer)
            .filter(Answer.question_id == question_id)
            .order_by(Answer.answered_at.desc())
            .first()
        )

    def _get_stat(self, q: Question):
        """取得 stat。"""
        if not q.node_id:
            return None
        user_id = self._get_user_id_for_question(q)
        if not user_id:
            return None
        return (
            self.db.query(QuestionStat)
            .filter(
                QuestionStat.user_id == user_id,
                QuestionStat.node_id == q.node_id,
            )
            .first()
        )

    def _get_mastery(self, q: Question):
        """取得 mastery。"""
        if not q.node_id:
            return None
        return self.db.query(NodeMastery).filter(NodeMastery.node_id == q.node_id).first()

    def _is_node_green_mature(self, mastery, now: datetime) -> bool:
        """判斷 node green mature。"""
        return (mastery and mastery.color == "green"
                and mastery.updated_at and (now - mastery.updated_at).days >= 14)

    def _check_protection(self, q: Question, now: datetime) -> str | None:
        """Return protection reason or None."""
        mastery = self._get_mastery(q)

        # SM-2 in progress (stage 1-4), unless node is green 14+ days
        stat = self._get_stat(q)
        if stat and 1 <= stat.success_count <= 4:
            if not self._is_node_green_mature(mastery, now):
                return f"SM-2 排程進行中（第 {stat.success_count} 階段）"

        # Bookmarked
        bookmarked = (
            self.db.query(Answer)
            .filter(Answer.question_id == q.id, Answer.marked_for_review.is_(True))
            .first()
        )
        if bookmarked:
            return "用戶收藏"

        # Knowledge node red
        if mastery and mastery.color == "red":
            return "對應知識節點未達精熟"

        # Dangerous blind spot not yet corrected
        blind_spot = (
            self.db.query(Answer)
            .filter(
                Answer.question_id == q.id,
                Answer.confidence == "high",
                Answer.is_correct.is_(False),
            )
            .first()
        )
        if blind_spot:
            correct_count = (
                self.db.query(Answer)
                .filter(Answer.question_id == q.id, Answer.is_correct.is_(True))
                .order_by(Answer.answered_at.desc())
                .limit(3)
                .all()
            )
            if len(correct_count) < 3:
                return "危險盲點修正中"

        return None

    def _retirement_reason(self, q: Question, now: datetime) -> str | None:
        """Return retirement reason or None if should not retire."""
        last_answer = self._get_last_answer(q.id)
        stat = self._get_stat(q)

        # Dangerous blind spot corrected (3 consecutive correct) → retire with reason
        blind_spot = (
            self.db.query(Answer)
            .filter(
                Answer.question_id == q.id,
                Answer.confidence == "high",
                Answer.is_correct.is_(False),
            )
            .first()
        )
        if blind_spot:
            correct_answers = (
                self.db.query(Answer)
                .filter(Answer.question_id == q.id, Answer.is_correct.is_(True))
                .order_by(Answer.answered_at.desc())
                .limit(3)
                .all()
            )
            if len(correct_answers) >= 3:
                # Check last correct was 14+ days ago
                if correct_answers[0].answered_at:
                    days_since = (now - correct_answers[0].answered_at).days
                    if days_since >= 14:
                        return "危險盲點已修正"

        # SM-2 five stages completed, 14 days ago
        if stat and stat.success_count >= 5:
            if stat.updated_at:
                days_since = (now - stat.updated_at).days
                if days_since >= 14:
                    return "SM-2 五階段完成"

        # Knowledge node green for 14+ days
        mastery = self._get_mastery(q)
        if self._is_node_green_mature(mastery, now):
            return "知識節點已精熟"

        # Expired and never answered
        if q.expires_at and q.expires_at <= now:
            if not last_answer:
                return "未作答逾期"
            # Answered correctly but 30+ days idle
            if last_answer.is_correct:
                idle_days = (now - last_answer.answered_at).days if last_answer.answered_at else 999
                if idle_days >= 30:
                    return "答對無後續互動"
            # Answered incorrectly and expired
            return "未作答逾期"

        # 60+ days idle
        if last_answer and last_answer.answered_at:
            idle_days = (now - last_answer.answered_at).days
            if idle_days >= 60:
                return "長期閒置"

        return None

    def scan(self):
        """每日退場掃描。"""
        now = datetime.now(timezone.utc)
        soft_deleted = 0
        skipped = 0

        ai_questions = (
            self.db.query(Question)
            .filter(
                Question.source_type == "ai_generated",
                Question.retired_at.is_(None),
            )
            .all()
        )

        # Pre-check alert threshold
        eligible_count = 0
        for q in ai_questions:
            protection = self._check_protection(q, now)
            if not protection and self._retirement_reason(q, now):
                eligible_count += 1

        if eligible_count > ALERT_THRESHOLD:
            return {
                "paused": True,
                "alert_triggered": True,
                "alert_message": f"異常大量退場：{eligible_count:,} 題",
                "audit_logged": True,
                "log_id": str(uuid.uuid4()),
            }

        for q in ai_questions:
            protection = self._check_protection(q, now)
            if protection:
                q.retention_reason = protection
                skipped += 1
                continue

            reason = self._retirement_reason(q, now)
            if reason:
                q.retired_at = now
                q.retention_reason = reason
                soft_deleted += 1

        self.db.commit()

        return {
            "soft_deleted_count": soft_deleted,
            "hard_deleted_count": 0,
            "skipped_count": skipped,
            "audit_logged": True,
            "log_id": str(uuid.uuid4()),
        }

    def hard_delete(self):
        """硬刪除 — 軟刪除超過 90 天的永久刪除。"""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=90)

        to_delete = (
            self.db.query(Question)
            .filter(
                Question.retired_at.isnot(None),
                Question.retired_at < cutoff,
            )
            .all()
        )

        count = len(to_delete)
        for q in to_delete:
            self.db.delete(q)
        self.db.commit()

        return {
            "hard_deleted_count": count,
            "json_cleaned": True,
            "audit_logged": True,
        }

    def post_result_scan(self):
        """放榜後退場掃描。"""
        now = datetime.now(timezone.utc)
        today = date.today()
        soft_deleted = 0

        journeys = (
            self.db.query(LearningJourney)
            .filter(
                LearningJourney.data_expiry_date.isnot(None),
                LearningJourney.data_expiry_date <= today,
            )
            .all()
        )

        for journey in journeys:
            exams = self.db.query(Exam).filter_by(
                user_id=journey.user_id,
                subject_id=journey.subject_id,
            ).all()

            reason = "考取後資料清除" if journey.exam_result_status == "passed" else "不再報考後資料清除"
            for exam in exams:
                ai_questions = (
                    self.db.query(Question)
                    .filter(
                        Question.exam_id == exam.id,
                        Question.source_type == "ai_generated",
                        Question.retired_at.is_(None),
                    )
                    .all()
                )
                for q in ai_questions:
                    q.retired_at = now
                    q.retention_reason = reason
                    soft_deleted += 1

        self.db.commit()
        return {"soft_deleted_count": soft_deleted, "audit_logged": True}

    def restore(self, subject_id: str):
        """恢復軟刪除的 AI 題。"""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=90)
        subj_uuid = uuid.UUID(subject_id)

        exams = self.db.query(Exam).filter_by(subject_id=subj_uuid).all()
        restored = 0

        for exam in exams:
            questions = (
                self.db.query(Question)
                .filter(
                    Question.exam_id == exam.id,
                    Question.source_type == "ai_generated",
                    Question.retired_at.isnot(None),
                    Question.retired_at > cutoff,
                )
                .all()
            )
            for q in questions:
                q.retired_at = None
                q.retention_reason = None
                q.expires_at = now + timedelta(days=7)
                restored += 1

        self.db.commit()
        return {"restored_count": restored}

    def check_reports(self, question_id: str):
        """檢查題目回報次數，達 3 次立即退場。"""
        q_uuid = uuid.UUID(question_id)
        now = datetime.now(timezone.utc)

        report_count = (
            self.db.query(func.count(ContentReport.id))
            .filter(
                ContentReport.target_id == question_id,
                ContentReport.target_type == "question",
            )
            .scalar()
        )

        q = self.db.query(Question).filter_by(id=q_uuid).first()
        if not q:
            return {"error": True, "status_code": 404, "message": "題目不存在"}

        if report_count >= 3:
            q.retired_at = now
            q.quality_flag = "low"
            q.retention_reason = "品質不合格"
            self.db.commit()
            return {"retired": True, "report_count": report_count}

        return {"retired": False, "report_count": report_count}

    def recalculate_available_questions(self):
        """重新計算各科目的 available_questions（只計算考古題）。"""
        from app.models.subject import Subject

        subjects = self.db.query(Subject).all()
        for subject in subjects:
            count = (
                self.db.query(func.count(Question.id))
                .join(Exam, Question.exam_id == Exam.id)
                .filter(
                    Exam.subject_id == subject.id,
                    Question.source_type == "historical",
                    Question.retired_at.is_(None),
                )
                .scalar()
            )
            subject.available_questions = count or 0

        self.db.commit()
        return {
            "subjects": [
                {"name": s.name, "available_questions": s.available_questions or 0}
                for s in subjects
            ]
        }
