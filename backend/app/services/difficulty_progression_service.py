"""Difficulty Progression Service — 階層式難度遞進業務邏輯。"""

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.exam import Exam
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.question import Question
from app.models.user import User


# Default thresholds
BACKTRACK_WRONG_THRESHOLD = 2
PROGRESS_CORRECT_THRESHOLD = 3
BACKTRACK_RATE_THRESHOLD = 40

# Difficulty mapping by depth
DEPTH_DIFFICULTY = {1: "easy", 2: "medium", 3: "hard"}


class DifficultyProgressionService:

    def __init__(self, db: Session):
        self.db = db

    def _get_user(self, user_id: str) -> User:
        return self.db.query(User).filter_by(id=uuid.UUID(user_id)).first()

    def _get_plan(self, user: User) -> str:
        return user.subscription_plan.value if hasattr(user.subscription_plan, "value") else str(user.subscription_plan)

    # ========== Start Adaptive Practice ==========

    def start_adaptive(self, user_id: str, subject_id: str) -> dict:
        user = self._get_user(user_id)
        plan = self._get_plan(user)

        # Check subscription
        if plan == "FREE":
            return {
                "error": True,
                "status_code": 403,
                "message": "自適應難度遞進功能為 PRO_PLUS 以上方案專屬",
            }

        return {"message": "自適應練習已開始", "status": "started"}

    # ========== Calculate Next Strategy ==========

    def calculate_next_strategy(
        self,
        user_id: str,
        subject_id: str,
        current_node_id: str,
        original_node_id: Optional[str] = None,
        consecutive_wrong: int = 0,
        consecutive_correct: int = 0,
    ) -> dict:
        uid = uuid.UUID(user_id)
        sid = uuid.UUID(subject_id)
        current_nid = uuid.UUID(current_node_id)

        current_node = self.db.query(KnowledgeNode).filter_by(id=current_nid).first()
        if not current_node:
            return {"error": True, "status_code": 404, "message": "節點不存在"}

        original_nid = uuid.UUID(original_node_id) if original_node_id else current_nid
        original_node = self.db.query(KnowledgeNode).filter_by(id=original_nid).first()

        # Check mastery rate for rate-based backtracking
        mastery = self.db.query(NodeMastery).filter_by(
            user_id=uid, node_id=current_nid
        ).first()

        should_backtrack = False
        should_progress = False
        reason = None

        # Check backtrack conditions
        if consecutive_wrong >= BACKTRACK_WRONG_THRESHOLD:
            should_backtrack = True
            reason = "連續答錯，需鞏固基礎"
        elif mastery and mastery.total_count > 0:
            rate = float(mastery.mastery_rate)
            if rate < BACKTRACK_RATE_THRESHOLD:
                should_backtrack = True
                reason = f"答對率過低（{rate}%），需鞏固基礎"

        # Check progress conditions
        if not should_backtrack and consecutive_correct >= PROGRESS_CORRECT_THRESHOLD:
            if original_node_id and str(current_nid) != str(original_nid):
                should_progress = True
                reason = "基礎已鞏固，挑戰進階題"

        # Determine next action
        if should_backtrack:
            # Find parent node
            parent_node = None
            if current_node.parent_id:
                parent_node = self.db.query(KnowledgeNode).filter_by(
                    id=current_node.parent_id
                ).first()

            if parent_node:
                difficulty = DEPTH_DIFFICULTY.get(parent_node.depth, "medium")
                result = {
                    "next_action": "backtrack",
                    "current_node": parent_node.name,
                    "current_node_id": str(parent_node.id),
                    "current_depth": parent_node.depth,
                    "original_node": original_node.name if original_node else current_node.name,
                    "difficulty": difficulty,
                    "backtrack_from": current_node.name,
                    "backtrack_to": parent_node.name,
                    "backtrack_count": 1,
                    "reason": reason,
                }
            else:
                # Already at root - stay
                difficulty = DEPTH_DIFFICULTY.get(current_node.depth, "easy")
                result = {
                    "next_action": "stay",
                    "current_node": current_node.name,
                    "current_node_id": str(current_node.id),
                    "current_depth": current_node.depth,
                    "original_node": original_node.name if original_node else current_node.name,
                    "difficulty": difficulty,
                    "backtrack_count": 0,
                    "hint": "建議複習此章節的基礎教材",
                }
        elif should_progress:
            # Find the child node closer to original
            target_node = self._find_progress_target(current_node, original_node)
            if target_node:
                difficulty = DEPTH_DIFFICULTY.get(target_node.depth, "medium")
                result = {
                    "next_action": "progress",
                    "current_node": target_node.name,
                    "current_node_id": str(target_node.id),
                    "current_depth": target_node.depth,
                    "original_node": original_node.name if original_node else current_node.name,
                    "difficulty": difficulty,
                    "progress_from": current_node.name,
                    "progress_to": target_node.name,
                    "backtrack_count": 0,
                    "reason": reason,
                }
            else:
                difficulty = DEPTH_DIFFICULTY.get(current_node.depth, "medium")
                result = {
                    "next_action": "stay",
                    "current_node": current_node.name,
                    "current_node_id": str(current_node.id),
                    "current_depth": current_node.depth,
                    "original_node": original_node.name if original_node else current_node.name,
                    "difficulty": difficulty,
                    "backtrack_count": 0,
                }
        else:
            # Stay at current node
            difficulty = DEPTH_DIFFICULTY.get(current_node.depth, "medium")
            result = {
                "next_action": "stay",
                "current_node": current_node.name,
                "current_node_id": str(current_node.id),
                "current_depth": current_node.depth,
                "original_node": original_node.name if original_node else current_node.name,
                "difficulty": difficulty,
                "backtrack_count": 0,
            }

        # Add a question from the target node
        target_nid = uuid.UUID(result["current_node_id"])
        question = self._pick_question(uid, sid, target_nid)
        if question:
            result["question"] = {
                "question_id": str(question.id),
                "content": question.content,
                "options": {
                    "A": question.option_a,
                    "B": question.option_b,
                    "C": question.option_c,
                    "D": question.option_d,
                },
                "source_type": question.source_type,
                "node_name": result["current_node"],
            }

        return result

    def _find_progress_target(self, current_node, original_node):
        """Find the next node to progress to (child of current toward original)."""
        if not original_node:
            return None

        # Walk from original up to find the child of current_node
        node = original_node
        while node and node.parent_id:
            if node.parent_id == current_node.id:
                return node
            node = self.db.query(KnowledgeNode).filter_by(id=node.parent_id).first()

        # If original is direct child of current
        if original_node.parent_id == current_node.id:
            return original_node

        return original_node

    def _pick_question(self, user_id, subject_id, node_id):
        """Pick a question from the given node."""
        return (
            self.db.query(Question)
            .filter(Question.node_id == node_id)
            .first()
        )

    # ========== Learning Trail ==========

    def get_trail(self, user_id: str, subject_id: str) -> dict:
        uid = uuid.UUID(user_id)
        sid = uuid.UUID(subject_id)

        # Get recent answers with their questions and nodes
        answers = (
            self.db.query(Answer, Question)
            .join(Question, Answer.question_id == Question.id)
            .join(Exam, Answer.exam_id == Exam.id)
            .filter(
                Answer.user_id == uid,
                Exam.subject_id == sid,
            )
            .order_by(Answer.answered_at)
            .all()
        )

        # Group consecutive answers by node into trail entries
        trail = []
        prev_node_id = None
        current_group = None

        for answer, question in answers:
            node = self.db.query(KnowledgeNode).filter_by(id=question.node_id).first()
            node_name = node.name if node else "unknown"

            if question.node_id == prev_node_id and current_group:
                # Same node — extend current group
                current_group["answer_count"] += 1
                if answer.is_correct:
                    current_group["correct_count"] += 1
            else:
                # New node — determine action and start new group
                if prev_node_id is None:
                    action = "answer"
                else:
                    prev_node = self.db.query(KnowledgeNode).filter_by(id=prev_node_id).first()
                    if prev_node and node:
                        if node.depth < prev_node.depth:
                            action = "backtrack"
                        elif node.depth > prev_node.depth:
                            action = "progress"
                        else:
                            action = "answer"
                    else:
                        action = "answer"

                current_group = {
                    "node_name": node_name,
                    "action": action,
                    "answer_count": 1,
                    "correct_count": 1 if answer.is_correct else 0,
                }
                trail.append(current_group)
                prev_node_id = question.node_id

        return {"trail": trail}
