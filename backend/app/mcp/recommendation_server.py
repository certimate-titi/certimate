"""Recommendation Server MCP — Provides intelligent question selection and scheduling."""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.mcp.base_server import BaseMCPServer
from app.mcp.types import (
    RecommendedQuestion,
    SpacingCalculation,
    LearningPathItem,
    NodeQualityValidation,
    MCPResponse,
    MCPErrorType,
)

# Import models
from app.models.user import User
from app.models.answer import Answer
from app.models.question import Question
from app.models.exam import Exam
from app.models.subject import Subject
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery


class RecommendationServer(BaseMCPServer):
    """MCP Server for intelligent recommendations.

    Provides functions for:
    - Question recommendation based on mastery and difficulty
    - Spaced repetition scheduling (Ebbinghaus curve)
    - Learning path suggestions
    - Knowledge node quality validation
    """

    # Ebbinghaus intervals (days): 1, 3, 7, 14, 30, 60, 120
    EBBINGHAUS_INTERVALS = [1, 3, 7, 14, 30, 60, 120]

    def recommend_questions(
        self,
        user_id: str,
        count: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """
        Recommend questions based on user mastery and learning goals.

        Considers: mastery score, Bloom taxonomy level, spacing intervals,
        prerequisite knowledge, and confidence calibration goals.

        Args:
            user_id: UUID of the user
            count: Number of questions to recommend (default 5)
            filters: Optional filters (topic, min_difficulty, max_difficulty, bloom_level)

        Returns:
            MCPResponse with list of RecommendedQuestion
        """
        function_name = "recommend_questions"
        self.log_function_call(function_name, user_id=user_id, count=count)

        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return self.error(
                    f"User {user_id} not found",
                    MCPErrorType.NOT_FOUND,
                    {"user_id": user_id}
                )

            if not filters:
                filters = {}

            # Get candidate questions
            query = self.db.query(Question).join(
                Exam, Question.exam_id == Exam.id
            ).filter(
                Exam.user_id == user_id
            )

            # Apply filters
            if "topic" in filters:
                query = query.join(Subject, Exam.subject_id == Subject.id).filter(
                    Subject.name.ilike(f"%{filters['topic']}%")
                )

            if "min_difficulty" in filters:
                query = query.filter(Question.difficulty >= filters["min_difficulty"])

            if "max_difficulty" in filters:
                query = query.filter(Question.difficulty <= filters["max_difficulty"])

            if "bloom_level" in filters:
                query = query.filter(Question.bloom_category == filters["bloom_level"])

            questions = query.limit(count * 3).all()  # Get more to rank

            if not questions:
                return self.ok([])

            # Score and rank questions
            ranked_questions = []

            for question in questions:
                # Get last attempt for this question
                last_attempt = self.db.query(Answer).filter(
                    and_(
                        Answer.question_id == question.id,
                        Answer.user_id == user_id
                    )
                ).order_by(desc(Answer.answered_at)).first()

                # Calculate scores
                mastery_score = self._get_question_mastery(user_id, question.id)
                is_prerequisite_ready = self._check_prerequisites_ready(
                    user_id, question
                )
                should_calibrate_confidence = self._should_calibrate_confidence(
                    user_id, question.id, last_attempt
                )

                # Determine spacing recommendation
                if last_attempt:
                    days_since_last = (datetime.now() - last_attempt.answered_at).days
                    spacing_days = self._calculate_optimal_spacing(
                        user_id, question.id, last_attempt.confidence
                    ).days_from_today
                else:
                    days_since_last = 999  # New question
                    spacing_days = 0

                # Calculate recommendation score (higher is better)
                # Prioritize: spaced repetition due > prerequisite ready > low mastery > calibration
                score = 0.0
                if days_since_last >= spacing_days:
                    score += 100  # Due for review
                if is_prerequisite_ready:
                    score += 50
                score += (1 - mastery_score) * 30  # Prioritize weak areas
                if should_calibrate_confidence:
                    score += 20

                reason_parts = []
                if days_since_last >= spacing_days:
                    reason_parts.append("Due for spaced repetition")
                if mastery_score < 0.6:
                    reason_parts.append(f"Low mastery ({mastery_score:.0%})")
                if should_calibrate_confidence:
                    reason_parts.append("Confidence calibration needed")

                reason = "; ".join(reason_parts) if reason_parts else "Recommended for practice"

                exam = self.db.query(Exam).filter(Exam.id == question.exam_id).first()
                subject = None
                if exam:
                    subject = self.db.query(Subject).filter(
                        Subject.id == exam.subject_id
                    ).first()

                recommended = RecommendedQuestion(
                    question_id=str(question.id),
                    topic=subject.name if subject else "Unknown",
                    difficulty_level=self._map_difficulty_to_level(question.difficulty),
                    bloom_level=question.bloom_category or "understand",
                    reason=reason,
                    mastery_score=mastery_score,
                    spacing_days=spacing_days,
                    prerequisite_ready=is_prerequisite_ready,
                    confidence_calibration_ready=should_calibrate_confidence
                )

                ranked_questions.append((score, recommended))

            # Sort by score and return top N
            ranked_questions.sort(key=lambda x: x[0], reverse=True)
            result = [q[1].to_dict() for q in ranked_questions[:count]]

            return self.ok(result)

        except Exception as e:
            return self.error(
                f"Failed to recommend questions: {str(e)}",
                MCPErrorType.INTERNAL_ERROR,
                {"user_id": user_id, "error": str(e)}
            )

    def calculate_optimal_spacing(
        self,
        user_id: str,
        question_id: str
    ) -> MCPResponse:
        """
        Calculate optimal spaced repetition interval using Ebbinghaus curve.

        Considers: last attempt, confidence level, mastery threshold.

        Args:
            user_id: UUID of the user
            question_id: UUID of the question

        Returns:
            MCPResponse with SpacingCalculation
        """
        function_name = "calculate_optimal_spacing"
        self.log_function_call(function_name, user_id=user_id, question_id=question_id)

        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return self.error(
                    f"User {user_id} not found",
                    MCPErrorType.NOT_FOUND
                )

            question = self.db.query(Question).filter(
                Question.id == question_id
            ).first()
            if not question:
                return self.error(
                    f"Question {question_id} not found",
                    MCPErrorType.NOT_FOUND
                )

            last_attempt = self.db.query(Answer).filter(
                and_(
                    Answer.question_id == question_id,
                    Answer.user_id == user_id
                )
            ).order_by(desc(Answer.answered_at)).first()

            spacing_calc = self._calculate_optimal_spacing(
                user_id, question_id, last_attempt.confidence if last_attempt else None
            )

            return self.ok(spacing_calc.to_dict())

        except Exception as e:
            return self.error(
                f"Failed to calculate spacing: {str(e)}",
                MCPErrorType.INTERNAL_ERROR
            )

    def suggest_learning_path(
        self,
        user_id: str,
        target_topic: str
    ) -> MCPResponse:
        """
        Suggest a learning path to master a topic.

        Returns dependency-aware sequence with prerequisite ordering.

        Args:
            user_id: UUID of the user
            target_topic: Target topic to learn

        Returns:
            MCPResponse with list of LearningPathItem
        """
        function_name = "suggest_learning_path"
        self.log_function_call(function_name, user_id=user_id, target_topic=target_topic)

        try:
            # For now, return a simple sequential path
            # TODO: Implement knowledge graph traversal for prerequisites
            path = [
                LearningPathItem(
                    topic=target_topic,
                    concept_id="root",
                    prerequisites=[],
                    difficulty=5,
                    estimated_hours=3.0,
                    is_prerequisite_met=True,
                    mastery_progress=0.0
                )
            ]

            return self.ok([item.to_dict() for item in path])

        except Exception as e:
            return self.error(
                f"Failed to suggest learning path: {str(e)}",
                MCPErrorType.INTERNAL_ERROR
            )

    def validate_knowledge_node_quality(
        self,
        node_data: Dict[str, Any]
    ) -> MCPResponse:
        """
        Validate quality of a generated knowledge node.

        Checks: concept clarity, example validity, relationship correctness.

        Args:
            node_data: Knowledge node data to validate

        Returns:
            MCPResponse with NodeQualityValidation
        """
        function_name = "validate_knowledge_node_quality"
        self.log_function_call(function_name)

        try:
            issues = []
            score = 1.0
            recommendations = []

            # Check concept name
            if "concept_name" not in node_data or not node_data["concept_name"]:
                issues.append({
                    "type": "missing_concept_name",
                    "severity": "high"
                })
                score -= 0.3
                recommendations.append("Add clear concept name")

            # Check definition
            if "definition" not in node_data or not node_data["definition"]:
                issues.append({
                    "type": "missing_definition",
                    "severity": "high"
                })
                score -= 0.3
                recommendations.append("Add comprehensive definition")

            # Check examples
            examples = node_data.get("examples", [])
            if not examples or len(examples) == 0:
                issues.append({
                    "type": "missing_examples",
                    "severity": "medium"
                })
                score -= 0.2
                recommendations.append("Add at least 2-3 concrete examples")
            elif len(examples) < 2:
                issues.append({
                    "type": "insufficient_examples",
                    "severity": "low"
                })
                score -= 0.1
                recommendations.append("Add more examples for clarity")

            # Check relationships
            relationships = (
                node_data.get("related_concepts", []) +
                node_data.get("prerequisite_concepts", [])
            )
            if not relationships:
                issues.append({
                    "type": "missing_relationships",
                    "severity": "low"
                })
                score -= 0.1
                recommendations.append("Add related or prerequisite concepts")

            score = max(0.0, min(1.0, score))

            validation = NodeQualityValidation(
                is_valid=score >= 0.6,
                issues=issues,
                score=score,
                recommendations=recommendations
            )

            return self.ok(validation.to_dict())

        except Exception as e:
            return self.error(
                f"Failed to validate node quality: {str(e)}",
                MCPErrorType.INTERNAL_ERROR
            )

    # ======================== Helper Methods ========================

    def _get_question_mastery(self, user_id: str, question_id: str) -> float:
        """Get user's mastery score for a specific question (0-1)."""
        attempts = self.db.query(Answer).filter(
            and_(
                Answer.question_id == question_id,
                Answer.user_id == user_id
            )
        ).all()

        if not attempts:
            return 0.5  # Unknown - neutral score

        correct = sum(1 for a in attempts if a.is_correct)
        return correct / len(attempts)

    def _check_prerequisites_ready(self, user_id: str, question: Question) -> bool:
        """Check if user has mastered all prerequisites for a question."""
        # TODO: Implement when knowledge graph relationships are available
        return True

    def _should_calibrate_confidence(
        self,
        user_id: str,
        question_id: str,
        last_attempt: Optional[Answer]
    ) -> bool:
        """Check if user needs confidence calibration for this question."""
        if not last_attempt:
            return True

        # Check if confidence matches reality
        if last_attempt.confidence == "high" and not last_attempt.is_correct:
            return True  # Overconfident
        if last_attempt.confidence == "low" and last_attempt.is_correct:
            return True  # Underconfident

        return False

    def _calculate_optimal_spacing(
        self,
        user_id: str,
        question_id: str,
        confidence: Optional[str]
    ) -> SpacingCalculation:
        """Calculate optimal review interval using Ebbinghaus curve."""
        last_attempt = self.db.query(Answer).filter(
            and_(
                Answer.question_id == question_id,
                Answer.user_id == user_id
            )
        ).order_by(desc(Answer.answered_at)).first()

        if not last_attempt:
            # First attempt - review in 1 day
            next_review = datetime.now() + timedelta(days=1)
            return SpacingCalculation(
                next_review_date=next_review.date().isoformat(),
                days_from_today=1,
                ebbinghaus_interval=1,
                reasoning="First attempt - initial review",
                confidence_factor=1.0
            )

        # Calculate attempt count for this question
        attempt_count = self.db.query(func.count(Answer.id)).filter(
            and_(
                Answer.question_id == question_id,
                Answer.user_id == user_id
            )
        ).scalar() or 0

        # Determine interval based on attempt count and correctness
        if not last_attempt.is_correct:
            interval_days = 1  # Reset for incorrect
        else:
            interval_idx = min(attempt_count - 1, len(self.EBBINGHAUS_INTERVALS) - 1)
            interval_days = self.EBBINGHAUS_INTERVALS[interval_idx]

        # Adjust based on confidence
        confidence_factor = 1.0
        if confidence and confidence == "low" and last_attempt.is_correct:
            confidence_factor = 1.2  # Extend interval if underconfident
        elif confidence and confidence == "high" and not last_attempt.is_correct:
            confidence_factor = 0.5  # Reduce interval if overconfident

        adjusted_days = max(1, int(interval_days * confidence_factor))
        next_review = datetime.now() + timedelta(days=adjusted_days)

        return SpacingCalculation(
            next_review_date=next_review.date().isoformat(),
            days_from_today=adjusted_days,
            ebbinghaus_interval=interval_days,
            reasoning=f"Ebbinghaus interval {interval_days} days, adjusted {confidence_factor}x for confidence",
            confidence_factor=confidence_factor
        )

    def _map_difficulty_to_level(self, difficulty: str) -> int:
        """Map difficulty enum to 1-10 scale."""
        difficulty_map = {
            "easy": 3,
            "medium": 5,
            "hard": 8
        }
        return difficulty_map.get(str(difficulty).lower(), 5)
