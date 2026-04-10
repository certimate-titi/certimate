"""
Context Server - 提供用户学习上下文给AI Coach
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.answer import Answer
from app.models.question import Question
from app.models.knowledge_node import KnowledgeNode
from app.mcp.base_server import BaseMCPServer
from app.mcp.types import WeakArea, UserContext, LearningStyle

logger = logging.getLogger("certimate.mcp.context")


class ContextServer(BaseMCPServer):
    """Context Server - 构建和提供用户学习上下文"""

    def _register_functions(self) -> None:
        """注册 Context Server 的所有函数"""
        self._register("BuildContextForCoach", self.build_context_for_coach)
        self._register("FetchWeakAreaDetails", self.fetch_weak_area_details)
        self._register("GetUserLearningStyle", self.get_user_learning_style)
        self._register("FetchRecentErrors", self.fetch_recent_errors)

    async def build_context_for_coach(self, user_id: str) -> dict:
        """
        为AI Coach构建完整的用户学习上下文

        返回:
            {
                "user_id": str,
                "display_name": str,
                "weak_areas": [{"topic": str, "mastery": float, "error_count": int}],
                "learning_style": str,
                "daily_study_minutes": int,
                "total_questions_answered": int,
                "average_accuracy": float,
                "error": bool (如果有错误)
            }
        """
        try:
            user_uuid = UUID(user_id)
            user = self.db.query(User).filter_by(id=user_uuid).first()

            if not user:
                return self.error(f"User not found: {user_id}")

            # 获取用户的弱点领域（最弱的3个）
            weak_areas = self._get_weak_topics(user_uuid, top_n=3)

            # 计算用户的总答题数和平均准确率
            total_answers = self.db.query(func.count(Answer.id)).filter(
                Answer.user_id == user_uuid
            ).scalar() or 0

            correct_answers = self.db.query(func.count(Answer.id)).filter(
                Answer.user_id == user_uuid,
                Answer.is_correct == True
            ).scalar() or 0

            average_accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0.0

            return self.success(
                data={
                    "user_id": str(user_uuid),
                    "display_name": user.display_name or user.email.split("@")[0],
                    "weak_areas": weak_areas,
                    "learning_style": getattr(user, "learning_style", "hybrid"),
                    "daily_study_minutes": getattr(user, "daily_study_minutes", 30),
                    "total_questions_answered": total_answers,
                    "average_accuracy": round(average_accuracy, 2),
                }
            )
        except ValueError as e:
            return self.error(f"Invalid user_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error building context for coach: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def fetch_weak_area_details(self, user_id: str, area_name: str) -> dict:
        """
        获取特定弱点领域的详细错误模式和频率

        参数:
            user_id: 用户 UUID
            area_name: 知识点名称

        返回:
            {
                "topic": str,
                "error_count": int,
                "error_patterns": [str],
                "last_error_at": str (ISO 8601),
                "mastery_score": float (0.0-1.0)
            }
        """
        try:
            user_uuid = UUID(user_id)

            # 查询该用户在该知识点上的所有错误
            rows = (
                self.db.query(
                    KnowledgeNode.name,
                    func.count(Answer.id).label("error_count"),
                    func.max(Answer.created_at).label("last_error_at"),
                )
                .join(Question, Question.node_id == KnowledgeNode.id)
                .join(Answer, Answer.question_id == Question.id)
                .filter(Answer.user_id == user_uuid)
                .filter(Answer.is_correct == False)
                .filter(KnowledgeNode.name == area_name)
                .group_by(KnowledgeNode.name)
                .first()
            )

            if not rows:
                return self.error(f"No error history found for area: {area_name}")

            error_count = rows[1]
            last_error_at = rows[2]
            mastery_score = max(0.1, 0.6 - 0.1 * min(error_count, 5))

            # 获取最近的5个错误的具体信息来分析错误模式
            error_patterns = self._analyze_error_patterns(user_uuid, area_name, limit=5)

            return self.success(
                data={
                    "topic": area_name,
                    "error_count": error_count,
                    "error_patterns": error_patterns,
                    "last_error_at": last_error_at.isoformat() if last_error_at else None,
                    "mastery_score": round(mastery_score, 3),
                }
            )
        except ValueError as e:
            return self.error(f"Invalid user_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching weak area details: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def get_user_learning_style(self, user_id: str) -> dict:
        """
        获取用户的学习风格和最优间隔复习参数

        返回:
            {
                "visual_preference": float (0.0-1.0),
                "kinesthetic_preference": float (0.0-1.0),
                "analytical_preference": float (0.0-1.0),
                "optimal_spacing_interval": int (天),
                "preferred_explanation_type": str
            }
        """
        try:
            user_uuid = UUID(user_id)
            user = self.db.query(User).filter_by(id=user_uuid).first()

            if not user:
                return self.error(f"User not found: {user_id}")

            # 基于用户的学习习惯推断学习风格
            # 这是一个简化版本；实际应用中可能有专门的学习风格评估
            learning_style = getattr(user, "learning_style", "hybrid")

            # 根据学习风格设置偏好
            style_preferences = {
                "visual": {"visual_preference": 0.8, "kinesthetic_preference": 0.3, "analytical_preference": 0.3},
                "kinesthetic": {"visual_preference": 0.3, "kinesthetic_preference": 0.8, "analytical_preference": 0.3},
                "analytical": {"visual_preference": 0.3, "kinesthetic_preference": 0.3, "analytical_preference": 0.8},
                "hybrid": {"visual_preference": 0.5, "kinesthetic_preference": 0.5, "analytical_preference": 0.5},
            }

            prefs = style_preferences.get(learning_style, style_preferences["hybrid"])

            # 艾宾浩斯遗忘曲线：2^n - 1 天
            # 基础间隔：1 天，3 天，7 天，15 天
            optimal_spacing = 3  # 默认3天

            return self.success(
                data={
                    "visual_preference": prefs["visual_preference"],
                    "kinesthetic_preference": prefs["kinesthetic_preference"],
                    "analytical_preference": prefs["analytical_preference"],
                    "optimal_spacing_interval": optimal_spacing,
                    "preferred_explanation_type": "with_examples",
                }
            )
        except ValueError as e:
            return self.error(f"Invalid user_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting user learning style: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def fetch_recent_errors(self, user_id: str, limit: int = 10) -> dict:
        """
        获取用户最近的错误记录

        参数:
            user_id: 用户 UUID
            limit: 返回记录数量

        返回:
            {
                "errors": [
                    {
                        "question_id": str,
                        "topic": str,
                        "error_at": str,
                        "user_answer": str,
                        "correct_answer": str
                    }
                ]
            }
        """
        try:
            user_uuid = UUID(user_id)

            # 获取最近的N个错误
            recent_errors = (
                self.db.query(
                    Answer.id,
                    Answer.question_id,
                    Answer.created_at,
                    Answer.selected_answer,
                    Question.correct_answer,
                    KnowledgeNode.name,
                )
                .join(Question, Answer.question_id == Question.id)
                .join(KnowledgeNode, Question.node_id == KnowledgeNode.id)
                .filter(Answer.user_id == user_uuid)
                .filter(Answer.is_correct == False)
                .order_by(desc(Answer.created_at))
                .limit(limit)
                .all()
            )

            errors_list = []
            for error in recent_errors:
                errors_list.append({
                    "question_id": str(error[1]),
                    "topic": error[5],
                    "error_at": error[2].isoformat() if error[2] else None,
                    "user_answer": error[3] or "Not recorded",
                    "correct_answer": error[4] or "Not recorded",
                })

            return self.success(
                data={"errors": errors_list}
            )
        except ValueError as e:
            return self.error(f"Invalid user_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching recent errors: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    # === Helper Methods ===

    def _get_weak_topics(self, user_id: UUID, top_n: int = 3) -> list[dict]:
        """从数据库查询用户最弱的知识点"""
        rows = (
            self.db.query(
                KnowledgeNode.name,
                func.count(Answer.id).label("error_count"),
            )
            .join(Question, Question.node_id == KnowledgeNode.id)
            .join(Answer, Answer.question_id == Question.id)
            .filter(Answer.user_id == user_id)
            .filter(Answer.is_correct == False)
            .group_by(KnowledgeNode.name)
            .order_by(func.count(Answer.id).desc())
            .limit(top_n)
            .all()
        )

        weak_areas = []
        for i, row in enumerate(rows):
            topic_name, error_count = row
            # 掌握度计算：错误越多，掌握度越低
            mastery = max(0.1, 0.6 - 0.1 * min(error_count, 5))
            weak_areas.append({
                "topic": topic_name,
                "mastery": round(mastery, 3),
                "error_count": error_count,
            })

        return weak_areas

    def _analyze_error_patterns(self, user_id: UUID, area_name: str, limit: int = 5) -> list[str]:
        """分析用户在特定领域的错误模式"""
        # 这是一个简化版本，实际应用中可能有更复杂的NLP分析
        patterns = []

        recent_errors = (
            self.db.query(
                Answer.selected_answer,
                Question.correct_answer,
                Question.text,
            )
            .join(Question, Answer.question_id == Question.id)
            .join(KnowledgeNode, Question.node_id == KnowledgeNode.id)
            .filter(Answer.user_id == user_id)
            .filter(Answer.is_correct == False)
            .filter(KnowledgeNode.name == area_name)
            .order_by(desc(Answer.created_at))
            .limit(limit)
            .all()
        )

        # 简单的模式检测：选择错误的特定答案
        for error in recent_errors:
            user_answer = error[0] or "empty"
            correct_answer = error[1] or "unknown"
            pattern = f"常选 {user_answer} 而非 {correct_answer}"
            if pattern not in patterns:
                patterns.append(pattern)

        return patterns[:3]  # 返回前3个模式
