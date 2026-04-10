"""
Recommendation Server - 智能问题推荐、间隔复习调度、学习路径建议
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.answer import Answer
from app.models.question import Question
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.mcp.base_server import BaseMCPServer

logger = logging.getLogger("certimate.mcp.recommendation")


class RecommendationServer(BaseMCPServer):
    """Recommendation Server - 问题推荐、间隔复习、学习路径"""

    def _register_functions(self) -> None:
        """注册 Recommendation Server 的所有函数"""
        self._register("RecommendQuestions", self.recommend_questions)
        self._register("CalculateOptimalSpacing", self.calculate_optimal_spacing)
        self._register("SuggestLearningPath", self.suggest_learning_path)
        self._register("ValidateKnowledgeNodeQuality", self.validate_knowledge_node_quality)

    async def recommend_questions(
        self,
        user_id: str,
        count: int = 5,
        filters: dict = None
    ) -> dict:
        """
        基于用户掌握度、Bloom分类学、难度推荐问题

        参数:
            user_id: 用户 UUID
            count: 推荐问题数量
            filters: 过滤条件 {
                "min_difficulty": 0.0-1.0,
                "max_difficulty": 0.0-1.0,
                "bloom_level": 1-6,
                "topic": str
            }

        返回:
            {
                "questions": [
                    {
                        "id": str,
                        "text": str,
                        "difficulty": float,
                        "topic": str,
                        "bloom_level": int,
                        "reason": str
                    }
                ],
                "total_recommended": int
            }
        """
        try:
            user_uuid = UUID(user_id)
            filters = filters or {}

            # 查询用户的掌握度信息
            user_masteries = (
                self.db.query(NodeMastery)
                .filter(NodeMastery.user_id == user_uuid)
                .all()
            )

            mastery_map = {um.node_id: um.base_mastery for um in user_masteries}

            # 构建查询：优先推荐掌握度低的知识点的问题
            query = self.db.query(
                Question.id,
                Question.text,
                Question.difficulty_level,
                Question.bloom_category,
                KnowledgeNode.name,
                NodeMastery.base_mastery,
            ).join(
                KnowledgeNode, Question.node_id == KnowledgeNode.id,
                isouter=True
            ).join(
                NodeMastery,
                and_(
                    NodeMastery.user_id == user_uuid,
                    NodeMastery.node_id == KnowledgeNode.id
                ),
                isouter=True
            ).filter(
                Question.is_active == True
            )

            # 应用过滤器
            if "topic" in filters:
                query = query.filter(KnowledgeNode.name == filters["topic"])

            # 按照掌握度排序（低掌握度优先）
            questions = query.order_by(
                func.coalesce(NodeMastery.base_mastery, 0.0).asc()
            ).limit(count * 2).all()  # 获取更多候选以增加多样性

            # 构建推荐列表，添加推荐理由
            recommended = []
            for q in questions[:count]:
                q_id, q_text, difficulty, bloom_level, topic, mastery = q
                mastery_score = mastery or 0.0

                # 推荐理由
                if mastery_score < 0.3:
                    reason = f"{topic} 掌握度低，需要重点突破"
                elif mastery_score < 0.6:
                    reason = f"{topic} 掌握度中等，需要加强"
                else:
                    reason = f"{topic} 定期复习以巩固"

                recommended.append({
                    "id": str(q_id),
                    "text": q_text[:100] if q_text else "N/A",  # 返回前100字
                    "difficulty": difficulty or "medium",
                    "topic": topic or "Unknown",
                    "bloom_level": self._bloom_level_to_number(bloom_level),
                    "reason": reason,
                })

            return self.success(
                data={
                    "questions": recommended,
                    "total_recommended": len(recommended),
                }
            )
        except ValueError as e:
            return self.error(f"Invalid user_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error recommending questions: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def calculate_optimal_spacing(
        self,
        user_id: str,
        question_id: str
    ) -> dict:
        """
        根据艾宾浩斯遗忘曲线计算最优复习时间

        参数:
            user_id: 用户 UUID
            question_id: 问题 UUID

        返回:
            {
                "question_id": str,
                "next_review_at": str (ISO 8601),
                "days_interval": int,
                "repetition_count": int
            }
        """
        try:
            user_uuid = UUID(user_id)
            question_uuid = UUID(question_id)

            # 获取问题的所有答题记录
            answers = (
                self.db.query(Answer)
                .filter(
                    Answer.user_id == user_uuid,
                    Answer.question_id == question_uuid
                )
                .order_by(desc(Answer.created_at))
                .all()
            )

            if not answers:
                # 如果没有答题记录，建议尽快复习（1天后）
                next_review = datetime.now(timezone.utc) + timedelta(days=1)
                return self.success(
                    data={
                        "question_id": question_id,
                        "next_review_at": next_review.isoformat(),
                        "days_interval": 1,
                        "repetition_count": 0,
                    }
                )

            # 计算重复次数
            repetition_count = len(answers)

            # 基于最后一次答题和正确性计算间隔
            last_answer = answers[0]
            days_since_last = (datetime.now(timezone.utc) - last_answer.created_at).days

            # 艾宾浩斯曲线间隔：1, 3, 7, 15, 30 天
            # 这是一个简化版本
            intervals = [1, 3, 7, 15, 30, 60, 120]

            if last_answer.is_correct:
                # 正确则延长间隔
                if repetition_count >= len(intervals):
                    days_interval = intervals[-1]  # 使用最长间隔
                else:
                    days_interval = intervals[repetition_count]
            else:
                # 错误则重置为1天
                days_interval = 1
                repetition_count = 0

            next_review = datetime.now(timezone.utc) + timedelta(days=days_interval)

            return self.success(
                data={
                    "question_id": question_id,
                    "next_review_at": next_review.isoformat(),
                    "days_interval": days_interval,
                    "repetition_count": repetition_count,
                }
            )
        except ValueError as e:
            return self.error(f"Invalid UUID format: {str(e)}")
        except Exception as e:
            logger.error(f"Error calculating spacing: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def suggest_learning_path(
        self,
        user_id: str,
        target_topic: str
    ) -> dict:
        """
        基于知识树依赖关系建议学习路径

        参数:
            user_id: 用户 UUID
            target_topic: 目标知识点名称

        返回:
            {
                "target_topic": str,
                "prerequisites": [str],  # 必须学习的前置知识
                "learning_sequence": [str],  # 推荐学习顺序
                "estimated_hours": float
            }
        """
        try:
            user_uuid = UUID(user_id)

            # 查找目标知识节点
            target_node = (
                self.db.query(KnowledgeNode)
                .filter(KnowledgeNode.name == target_topic)
                .first()
            )

            if not target_node:
                return self.error(f"Target topic not found: {target_topic}")

            # 获取前置知识（父节点）
            prerequisites = []
            current = target_node
            while current.parent_id:
                parent = self.db.query(KnowledgeNode).filter(
                    KnowledgeNode.id == current.parent_id
                ).first()
                if parent:
                    prerequisites.append(parent.name)
                    current = parent
                else:
                    break

            # 反向排序使得最基础的知识排在前面
            prerequisites.reverse()

            # 构建学习序列：前置知识 + 目标知识
            learning_sequence = prerequisites + [target_topic]

            # 估算学习时间（简化版本：每个主题2小时）
            estimated_hours = len(learning_sequence) * 2.0

            return self.success(
                data={
                    "target_topic": target_topic,
                    "prerequisites": prerequisites,
                    "learning_sequence": learning_sequence,
                    "estimated_hours": estimated_hours,
                }
            )
        except ValueError as e:
            return self.error(f"Invalid user_id format: {str(e)}")
        except Exception as e:
            logger.error(f"Error suggesting learning path: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    async def validate_knowledge_node_quality(
        self,
        node_data: dict
    ) -> dict:
        """
        验证知识节点的质量

        参数:
            node_data: {
                "name": str,
                "definition": str,
                "examples": [str],
                "relationships": [{"concept": str, "relation_type": str}]
            }

        返回:
            {
                "is_valid": bool,
                "issues": [str],
                "score": float (0.0-1.0)
            }
        """
        try:
            issues = []
            score = 1.0

            # 验证必要字段
            if not node_data.get("name"):
                issues.append("缺少 name 字段")
                score -= 0.25

            if not node_data.get("definition"):
                issues.append("缺少 definition 字段")
                score -= 0.25

            # 验证定义的清晰度
            definition = node_data.get("definition", "")
            if len(definition) < 20:
                issues.append("定义过短，可能不够清晰")
                score -= 0.1

            # 验证示例
            examples = node_data.get("examples", [])
            if not examples:
                issues.append("缺少示例")
                score -= 0.15
            elif len(examples) < 2:
                issues.append("示例数量不足（建议至少2个）")
                score -= 0.1

            # 验证关系
            relationships = node_data.get("relationships", [])
            if not relationships:
                issues.append("缺少与其他概念的关系")
                score -= 0.15

            # 验证关系的有效性
            for rel in relationships:
                if not rel.get("concept") or not rel.get("relation_type"):
                    issues.append("关系定义不完整")
                    score -= 0.05
                    break

            score = max(0.0, min(1.0, score))
            is_valid = score >= 0.6 and len(issues) == 0

            return self.success(
                data={
                    "is_valid": is_valid,
                    "issues": issues,
                    "score": round(score, 2),
                }
            )
        except Exception as e:
            logger.error(f"Error validating node quality: {str(e)}", exc_info=True)
            return self.error(f"Internal error: {str(e)}")

    # === Helper Methods ===

    def _bloom_level_to_number(self, bloom_category: str) -> int:
        """将Bloom分类转换为数字"""
        bloom_map = {
            "remember": 1,
            "understand": 2,
            "apply": 3,
            "analyze": 4,
            "evaluate": 5,
            "create": 6,
        }
        return bloom_map.get(bloom_category, 1)
