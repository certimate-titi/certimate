"""Context Server MCP — Provides structured user context for AI Coach and other services."""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.mcp.base_server import BaseMCPServer
from app.mcp.types import (
    CoachContext,
    WeakAreaDetail,
    LearningStyle,
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


class ContextServer(BaseMCPServer):
    """MCP Server for building structured user context.

    Provides functions for:
    - Building coach context (weak areas, mastery scores)
    - Fetching detailed weak area analysis
    - Getting user learning style
    - Retrieving recent errors with context
    """

    def build_context_for_coach(
        self,
        user_id: str,
        session_history: Optional[List[str]] = None
    ) -> MCPResponse:
        """
        Build structured learning context for AI Coach.

        Aggregates user's mastery scores, weak areas, recent errors, and learning streak.

        Args:
            user_id: UUID of the user
            session_history: Optional list of previous chat messages

        Returns:
            MCPResponse with CoachContext data
        """
        function_name = "build_context_for_coach"
        self.log_function_call(function_name, user_id=user_id)

        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return self.error(
                    f"User {user_id} not found",
                    MCPErrorType.NOT_FOUND,
                    {"user_id": user_id}
                )

            # Calculate mastery scores by subject
            mastery_scores = self._calculate_mastery_scores(user_id)

            # Identify weak areas (low mastery, high error rate)
            weak_areas = self._identify_weak_areas(user_id, mastery_scores)

            # Get recent errors
            recent_errors = self._fetch_recent_errors(user_id, limit=10)

            # Get learning style (if exists)
            learning_style = self._get_user_learning_style(user_id)

            # Calculate learning streak
            learning_streak = self._calculate_learning_streak(user_id)

            # Count total questions attempted
            total_questions = self.db.query(func.count(Answer.id)).filter(
                Answer.user_id == user_id
            ).scalar() or 0

            # Calculate average confidence
            avg_confidence_result = self.db.query(func.avg(
                func.nullif(Answer.confidence, None)
            )).filter(Answer.user_id == user_id).scalar()

            # Map confidence string to float (high=0.8, medium=0.5, low=0.2)
            avg_confidence = self._average_confidence_string_to_float(avg_confidence_result)

            context = CoachContext(
                user_id=user_id,
                weak_areas=weak_areas,
                mastery_scores=mastery_scores,
                recent_errors=recent_errors,
                learning_style=learning_style,
                learning_streak=learning_streak,
                total_questions_attempted=int(total_questions),
                average_confidence=avg_confidence
            )

            elapsed_ms = 0  # Will be set by decorator
            self.log_function_result(function_name, elapsed_ms, True, user_id=user_id)

            return self.ok(context.to_dict())

        except Exception as e:
            return self.error(
                f"Failed to build context: {str(e)}",
                MCPErrorType.INTERNAL_ERROR,
                {"user_id": user_id, "error": str(e)}
            )

    def fetch_weak_area_details(
        self,
        user_id: str,
        topic: str
    ) -> MCPResponse:
        """
        Fetch detailed analysis of a weak area.

        Returns error patterns, misconceptions, and recommendations.

        Args:
            user_id: UUID of the user
            topic: Topic name (e.g., "代數")

        Returns:
            MCPResponse with WeakAreaDetail
        """
        function_name = "fetch_weak_area_details"
        self.log_function_call(function_name, user_id=user_id, topic=topic)

        try:
            # Get all wrong answers for this user in this subject
            wrong_answers = self.db.query(Answer).join(
                Question, Answer.question_id == Question.id
            ).join(
                Exam, Answer.exam_id == Exam.id
            ).join(
                Subject, Exam.subject_id == Subject.id
            ).filter(
                and_(
                    Answer.user_id == user_id,
                    Answer.is_correct == False,
                    Subject.name.ilike(f"%{topic}%")
                )
            ).all()

            if not wrong_answers:
                return self.ok(WeakAreaDetail(
                    topic=topic,
                    error_rate=0.0,
                    total_attempts=0,
                    error_count=0,
                    misconceptions=[],
                    common_wrong_answers=[]
                ).to_dict())

            # Get all attempts (correct and incorrect) for this subject
            all_attempts = self.db.query(Answer).join(
                Question, Answer.question_id == Question.id
            ).join(
                Exam, Answer.exam_id == Exam.id
            ).join(
                Subject, Exam.subject_id == Subject.id
            ).filter(
                and_(
                    Answer.user_id == user_id,
                    Subject.name.ilike(f"%{topic}%")
                )
            ).all()

            error_rate = len(wrong_answers) / len(all_attempts) if all_attempts else 0.0
            error_count = len(wrong_answers)
            total_attempts = len(all_attempts)

            # Extract common wrong answers
            wrong_answer_options = {}
            for answer in wrong_answers:
                question = self.db.query(Question).filter(
                    Question.id == answer.question_id
                ).first()
                if question and answer.selected_answer:
                    key = answer.selected_answer
                    wrong_answer_options[key] = wrong_answer_options.get(key, 0) + 1

            common_wrong_answers = [
                {
                    "answer": option,
                    "frequency": count,
                    "percentage": round(count / error_count * 100, 1)
                }
                for option, count in sorted(
                    wrong_answer_options.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            ]

            # Get last attempt date
            last_attempt = max(
                (a.answered_at for a in all_attempts if a.answered_at),
                default=None
            )

            # Calculate confidence gap (if user is confident but gets it wrong)
            high_confidence_errors = sum(
                1 for a in wrong_answers if a.confidence == "high"
            )
            confidence_gap = high_confidence_errors / error_count if error_count > 0 else 0.0

            detail = WeakAreaDetail(
                topic=topic,
                error_rate=round(error_rate, 3),
                total_attempts=total_attempts,
                error_count=error_count,
                misconceptions=[],  # TODO: Extract from question explanations
                common_wrong_answers=common_wrong_answers,
                last_attempt_date=last_attempt.isoformat() if last_attempt else None,
                confidence_gap=round(confidence_gap, 3)
            )

            return self.ok(detail.to_dict())

        except Exception as e:
            return self.error(
                f"Failed to fetch weak area details: {str(e)}",
                MCPErrorType.INTERNAL_ERROR,
                {"user_id": user_id, "topic": topic}
            )

    def get_user_learning_style(self, user_id: str) -> MCPResponse:
        """
        Get user's learning style preferences.

        Args:
            user_id: UUID of the user

        Returns:
            MCPResponse with LearningStyle
        """
        function_name = "get_user_learning_style"
        self.log_function_call(function_name, user_id=user_id)

        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return self.error(
                    f"User {user_id} not found",
                    MCPErrorType.NOT_FOUND,
                    {"user_id": user_id}
                )

            # TODO: Load from user_preferences table once it's populated
            # For now, return defaults based on answer patterns
            learning_style = LearningStyle(
                preferred_modality="visual",  # Default
                optimal_spacing_days=3,
                preferred_explanation_style="example-driven",
                learning_pace="medium"
            )

            return self.ok(learning_style.to_dict())

        except Exception as e:
            return self.error(
                f"Failed to get learning style: {str(e)}",
                MCPErrorType.INTERNAL_ERROR,
                {"user_id": user_id}
            )

    def fetch_recent_errors(
        self,
        user_id: str,
        limit: int = 10
    ) -> MCPResponse:
        """
        Fetch recent wrong answers with full context.

        Args:
            user_id: UUID of the user
            limit: Maximum number of errors to return

        Returns:
            MCPResponse with list of error details
        """
        function_name = "fetch_recent_errors"
        self.log_function_call(function_name, user_id=user_id, limit=limit)

        try:
            errors = self._fetch_recent_errors(user_id, limit)
            return self.ok(errors)

        except Exception as e:
            return self.error(
                f"Failed to fetch recent errors: {str(e)}",
                MCPErrorType.INTERNAL_ERROR,
                {"user_id": user_id}
            )

    # ======================== Helper Methods ========================

    def _calculate_mastery_scores(self, user_id: str) -> Dict[str, float]:
        """Calculate user mastery score for each subject."""
        mastery = {}

        # Get all attempts by subject
        subject_attempts = self.db.query(
            Subject.name,
            func.count(Answer.id).label("total"),
            func.sum(func.cast(Answer.is_correct, type_=int)).label("correct")
        ).join(
            Exam, Answer.exam_id == Exam.id
        ).join(
            Subject, Exam.subject_id == Subject.id
        ).filter(
            Answer.user_id == user_id
        ).group_by(
            Subject.name
        ).all()

        for subject_name, total, correct in subject_attempts:
            correct_count = correct or 0
            mastery_score = correct_count / total if total > 0 else 0.0
            mastery[subject_name] = round(mastery_score, 2)

        return mastery

    def _identify_weak_areas(
        self,
        user_id: str,
        mastery_scores: Dict[str, float],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Identify topics where user is struggling (mastery below threshold)."""
        weak_areas = []

        for topic, score in mastery_scores.items():
            if score < threshold:
                # Get error count for this topic
                error_count = self.db.query(func.count(Answer.id)).join(
                    Question, Answer.question_id == Question.id
                ).join(
                    Exam, Answer.exam_id == Exam.id
                ).join(
                    Subject, Exam.subject_id == Subject.id
                ).filter(
                    and_(
                        Answer.user_id == user_id,
                        Answer.is_correct == False,
                        Subject.name == topic
                    )
                ).scalar() or 0

                # Get total attempts for this topic
                total_count = self.db.query(func.count(Answer.id)).join(
                    Question, Answer.question_id == Question.id
                ).join(
                    Exam, Answer.exam_id == Exam.id
                ).join(
                    Subject, Exam.subject_id == Subject.id
                ).filter(
                    and_(
                        Answer.user_id == user_id,
                        Subject.name == topic
                    )
                ).scalar() or 0

                error_rate = error_count / total_count if total_count > 0 else 0.0

                weak_areas.append({
                    "topic": topic,
                    "mastery": round(score, 2),
                    "error_rate": round(error_rate, 2),
                    "count": int(error_count)
                })

        return sorted(weak_areas, key=lambda x: x["mastery"])

    def _fetch_recent_errors(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent wrong answers with context."""
        recent_errors = []

        wrong_answers = self.db.query(Answer).filter(
            and_(
                Answer.user_id == user_id,
                Answer.is_correct == False
            )
        ).order_by(
            Answer.answered_at.desc()
        ).limit(limit).all()

        for answer in wrong_answers:
            question = self.db.query(Question).filter(
                Question.id == answer.question_id
            ).first()

            exam = self.db.query(Exam).filter(
                Exam.id == answer.exam_id
            ).first()

            subject = None
            if exam:
                subject = self.db.query(Subject).filter(
                    Subject.id == exam.subject_id
                ).first()

            recent_errors.append({
                "question_id": str(answer.question_id),
                "topic": subject.name if subject else "Unknown",
                "difficulty": question.difficulty if question else "unknown",
                "user_selected": answer.selected_answer or "No answer",
                "correct_answer": question.correct_answer if question else "Unknown",
                "user_confidence": answer.confidence or "not_set",
                "answered_at": answer.answered_at.isoformat() if answer.answered_at else None
            })

        return recent_errors

    def _calculate_learning_streak(self, user_id: str) -> int:
        """Calculate current learning streak (consecutive days with attempts)."""
        # Get all attempt dates
        attempt_dates = self.db.query(
            func.date(Answer.answered_at)
        ).filter(
            and_(
                Answer.user_id == user_id,
                Answer.answered_at.isnot(None)
            )
        ).distinct().order_by(
            func.date(Answer.answered_at).desc()
        ).all()

        if not attempt_dates:
            return 0

        streak = 1
        today = datetime.now().date()
        last_date = attempt_dates[0][0]

        # If last attempt wasn't today, streak is broken
        if last_date != today:
            if (today - last_date).days > 1:
                return 0
            streak = 1

        # Count consecutive days backwards
        for i in range(1, len(attempt_dates)):
            current_date = attempt_dates[i][0]
            previous_date = attempt_dates[i - 1][0]

            if (previous_date - current_date).days == 1:
                streak += 1
            else:
                break

        return streak

    def _get_user_learning_style(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user learning style preferences."""
        # TODO: Implement once user_preferences table is populated
        return None

    def _average_confidence_string_to_float(self, avg_str: Optional[str]) -> float:
        """Convert average confidence string to float."""
        if not avg_str:
            return 0.5

        # Map confidence to float
        confidence_map = {"high": 0.8, "medium": 0.5, "low": 0.2}
        return confidence_map.get(str(avg_str).lower(), 0.5)
