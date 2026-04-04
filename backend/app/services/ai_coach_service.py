"""進階 AI 教練 Service — ULTRA 方案專屬。

提供弱點分析、突破策略、7天衝刺計畫。
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from sqlalchemy import func

from app.models.user import User, SubscriptionPlan
from app.models.answer import Answer
from app.models.question import Question
from app.models.knowledge_node import KnowledgeNode

logger = logging.getLogger("certimate.ai_coach")


class AICoachService:
    def __init__(self, db: Session):
        self.db = db

    def _get_weak_topics(self, user_id: uuid.UUID, top_n: int = 3) -> list[dict]:
        """從實際錯題資料中查詢使用者最弱的知識節點。"""
        rows = (
            self.db.query(
                KnowledgeNode.name,
                func.count(Answer.id).label("error_count"),
            )
            .join(Question, Question.node_id == KnowledgeNode.id)
            .join(Answer, Answer.question_id == Question.id)
            .filter(Answer.user_id == user_id)
            .filter(Answer.is_correct == False)  # noqa: E712
            .group_by(KnowledgeNode.name)
            .order_by(func.count(Answer.id).desc())
            .limit(top_n)
            .all()
        )
        return [{"topic": r[0], "error_count": r[1]} for r in rows]

    def _validate_ultra(self, user_id: str) -> dict | User:
        """驗證用戶為 ULTRA 方案。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        if plan != "ULTRA":
            return {"error": True, "status_code": 403, "message": "進階 AI 教練為 ULTRA 方案專屬功能"}

        return user

    def get_advanced_analysis(self, user_id: str, subject_id: str | None = None) -> dict:
        """取得進階弱點分析 + 突破策略 + 衝刺計畫。"""
        result = self._validate_ultra(user_id)
        if isinstance(result, dict):
            return result
        user = result

        display_name = user.display_name or user.email.split("@")[0]
        daily_minutes = user.daily_study_minutes if hasattr(user, 'daily_study_minutes') and user.daily_study_minutes else 30
        learning_style = user.learning_style if hasattr(user, 'learning_style') and user.learning_style else "hybrid"

        # Query actual weak topics from DB
        user_uuid = uuid.UUID(user_id)
        db_weak = self._get_weak_topics(user_uuid, top_n=3)

        if db_weak:
            weakness_analysis = []
            for i, w in enumerate(db_weak):
                weakness_analysis.append({
                    "topic": w["topic"],
                    "mastery": max(0.1, 0.6 - 0.1 * w["error_count"]),
                    "error_pattern": f"{w['topic']} 相關題目答錯 {w['error_count']} 次",
                    "priority": i + 1,
                })
        else:
            weakness_analysis = [
                {"topic": "IAM 身分管理", "mastery": 0.35,
                 "error_pattern": "混淆 IAM Role 與 IAM Policy 的授權範圍", "priority": 1},
                {"topic": "VPC 網路設計", "mastery": 0.42,
                 "error_pattern": "Subnet CIDR 計算錯誤", "priority": 2},
                {"topic": "S3 儲存策略", "mastery": 0.55,
                 "error_pattern": "生命週期政策與版本控制混淆", "priority": 3},
            ]

        # Build breakthrough strategies based on actual weak topics
        strategy_templates = [
            ("使用角色扮演法：模擬不同角色的場景", "情境題 + 比較表", 3, "精緻化編碼"),
            ("視覺化練習：畫出架構圖或流程圖", "計算題 + 架構設計題", 2, "雙重編碼理論"),
            ("比較表整理：將各特性列表對照", "比較選擇題", 1.5, "交錯練習"),
        ]
        breakthrough_strategies = []
        for i, wa in enumerate(weakness_analysis):
            tpl = strategy_templates[i % len(strategy_templates)]
            breakthrough_strategies.append({
                "topic": wa["topic"],
                "method": tpl[0],
                "practice_type": tpl[1],
                "estimated_hours": tpl[2],
                "principle": tpl[3],
            })

        # Build sprint plan using the weak topics
        topics = [wa["topic"] for wa in weakness_analysis]
        sprint_plan = []
        for day in range(1, 8):
            if day <= 2:
                topic = topics[0] if topics else "綜合複習"
                practice_count = 15
            elif day <= 4:
                topic = topics[1] if len(topics) > 1 else topics[0] if topics else "綜合複習"
                practice_count = 12
            elif day <= 5:
                topic = topics[2] if len(topics) > 2 else topics[0] if topics else "綜合複習"
                practice_count = 10
            else:
                topic = "綜合複習"
                practice_count = 20

            review_items = []
            if day >= 3 and topics:
                review_items.append(f"{topics[0]} (間隔複習)")
            if day >= 5 and len(topics) > 1:
                review_items.append(f"{topics[1]} (間隔複習)")

            sprint_plan.append({
                "day": day,
                "topic": topic,
                "study_minutes": min(daily_minutes, 60),
                "practice_count": practice_count,
                "review_items": review_items,
            })

        return {
            "student_name": display_name,
            "daily_study_minutes": daily_minutes,
            "learning_style": learning_style,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "weakness_analysis": weakness_analysis,
            "breakthrough_strategies": breakthrough_strategies,
            "sprint_plan": sprint_plan,
        }

    def get_learning_history_summary(self, user_id: str, days: int = 30) -> dict:
        """取得用戶近 N 天的學習歷史摘要。"""
        result = self._validate_ultra(user_id)
        if isinstance(result, dict):
            return result
        user = result

        # TODO: 整合真實學習統計
        return {
            "user_id": user_id,
            "period_days": days,
            "total_exams": 0,
            "total_questions_answered": 0,
            "average_accuracy": None,
            "study_days": 0,
            "daily_average_minutes": 0,
        }
