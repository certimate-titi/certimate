"""學習記憶排程 Service。

MCP 整合：使用 Recommendation Server 提供基於掌握度的智能問題推薦。
艾賓浩斯遺忘曲線間隔複習排程。
"""

import uuid
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.learning_journey import LearningJourney
from app.models.subject import Subject
from app.mcp.recommendation_server import RecommendationServer
from app.mcp.base_server import MCPServerFactory

logger = logging.getLogger("certimate.schedule")


class ScheduleService:
    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(self, user_id: str):
        """查看學習排程建議。"""
        user_uuid = uuid.UUID(user_id)

        journeys = (
            self.db.query(LearningJourney, Subject)
            .join(Subject, Subject.id == LearningJourney.subject_id)
            .filter(LearningJourney.user_id == user_uuid)
            .filter(LearningJourney.is_archived == False)  # noqa: E712
            .all()
        )

        if not journeys:
            return {"error": True, "status_code": 400, "message": "請先在 Onboarding 或會員中心新增至少一個備考科目"}

        subjects = []
        for journey, subj in journeys:
            mode = self._calculate_mode(journey.exam_date, date.today())
            subjects.append({
                "subject_name": subj.name,
                "exam_date": journey.exam_date.isoformat() if journey.exam_date else None,
                "learning_mode": mode,
            })

        return {"subjects": subjects}

    def init_schedule(self, user_id: str, subject_id: str):
        """初始化排程。"""
        user_uuid = uuid.UUID(user_id)
        subj_uuid = uuid.UUID(subject_id)

        journey = self.db.query(LearningJourney).filter_by(
            user_id=user_uuid, subject_id=subj_uuid
        ).first()

        if not journey:
            return {"error": True, "status_code": 404, "message": "找不到該科目的學習歷程"}

        if not journey.exam_date:
            return {"error": True, "status_code": 400, "message": "必須設定考試日期才能初始化排程"}

        mode = self._calculate_mode(journey.exam_date, date.today())
        return {"message": "排程初始化完成", "learning_mode": mode}

    def calculate_mode(self, user_id: str, subject_id: str, today_str: str | None = None):
        """計算學習模式。"""
        user_uuid = uuid.UUID(user_id)
        subj_uuid = uuid.UUID(subject_id)

        journey = self.db.query(LearningJourney).filter_by(
            user_id=user_uuid, subject_id=subj_uuid
        ).first()

        if not journey:
            return {"error": True, "status_code": 404, "message": "找不到該科目的學習歷程"}

        today = date.fromisoformat(today_str) if today_str else date.today()
        mode = self._calculate_mode(journey.exam_date, today)

        return {"learning_mode": mode}

    def get_recommended_questions(self, user_id: str, count: int = 10) -> dict:
        """
        使用 MCP Recommendation Server 獲取基於掌握度的推薦問題。

        參數:
            user_id: 使用者 UUID
            count: 推薦問題數量

        返回:
            {
                "questions": [...],
                "total_recommended": int,
                "reasoning": str
            }
        """
        try:
            mcp_rec = MCPServerFactory.get_recommendation_server(self.db)
            response = mcp_rec.recommend_questions(user_id, count)

            if response.get("error"):
                logger.warning(f"MCP Recommendation failed: {response.get('message')}, using fallback")
                return self._get_recommended_questions_fallback(user_id, count)

            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error using MCP Recommendation Server: {str(e)}", exc_info=True)
            return self._get_recommended_questions_fallback(user_id, count)

    def get_spaced_repetition_schedule(self, user_id: str, question_id: str) -> dict:
        """
        使用 MCP Recommendation Server 計算艾賓浩斯間隔複習時間。

        參數:
            user_id: 使用者 UUID
            question_id: 問題 UUID

        返回:
            {
                "question_id": str,
                "next_review_at": str,
                "days_interval": int,
                "repetition_count": int
            }
        """
        try:
            mcp_rec = MCPServerFactory.get_recommendation_server(self.db)
            response = mcp_rec.calculate_optimal_spacing(user_id, question_id)

            if response.get("error"):
                logger.warning(f"MCP Spacing calculation failed: {response.get('message')}")
                return {"error": True, "status_code": 400, "message": response.get("message")}

            return {"error": False, "data": response.get("data", {})}
        except Exception as e:
            logger.error(f"Error calculating spacing: {str(e)}", exc_info=True)
            return {"error": True, "status_code": 500, "message": str(e)}

    def _calculate_mode(self, exam_date: date | None, today: date) -> str:
        """根據距考日天數計算學習模式。"""
        if not exam_date:
            return "standard"

        days_until = (exam_date - today).days

        if days_until <= 14:
            return "sprint"
        elif days_until <= 180:  # ~6 months
            return "standard"
        else:
            return "mastery"

    def _get_recommended_questions_fallback(self, user_id: str, count: int) -> dict:
        """當 MCP Recommendation Server 不可用時的降級方法。"""
        logger.info("Using fallback for question recommendations (MCP unavailable)")
        return {
            "questions": [],
            "total_recommended": 0,
            "reasoning": "MCP Recommendation Server unavailable - please try again later"
        }
