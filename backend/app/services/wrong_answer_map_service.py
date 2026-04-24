"""Wrong Answer Map Service — 個人化錯題地圖業務邏輯。"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.exam import Exam
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.question import Question
from app.models.user import User


class WrongAnswerMapService:

    def __init__(self, db: Session):
        self.db = db

    # ========== Helpers ==========

    def _get_user(self, user_id: str) -> User:
        return self.db.query(User).filter_by(id=uuid.UUID(user_id)).first()

    def _get_plan(self, user: User) -> str:
        return user.subscription_plan.value if hasattr(user.subscription_plan, "value") else str(user.subscription_plan)

    def _compute_color(self, rate: Optional[Decimal], total_count: int = 0) -> str:
        if total_count == 0 or rate is None:
            return "gray"
        r = float(rate)
        if r >= 80:
            return "green"
        elif r >= 60:
            return "orange"
        else:
            return "red"

    # ========== Update Mastery ==========

    def update_mastery(self, user_id: str, subject_id: str) -> dict:
        uid = uuid.UUID(user_id)
        sid = uuid.UUID(subject_id)

        # Get all nodes for this subject
        nodes = self.db.query(KnowledgeNode).filter_by(subject_id=sid).all()

        for node in nodes:
            # Count correct/total from answers for questions mapped to this node
            answers = (
                self.db.query(Answer)
                .join(Question, Answer.question_id == Question.id)
                .filter(
                    Answer.user_id == uid,
                    Question.node_id == node.id,
                )
                .all()
            )

            total = len(answers)
            correct = sum(1 for a in answers if a.is_correct)
            rate = Decimal(str(round(correct / total * 100, 2))) if total > 0 else Decimal("0")
            color = self._compute_color(rate, total)

            # Upsert mastery
            mastery = self.db.query(NodeMastery).filter_by(
                user_id=uid, node_id=node.id
            ).first()

            if mastery:
                mastery.correct_count = correct
                mastery.total_count = total
                mastery.mastery_rate = rate
                mastery.color = color
            else:
                mastery = NodeMastery(
                    user_id=uid,
                    node_id=node.id,
                    correct_count=correct,
                    total_count=total,
                    mastery_rate=rate,
                    color=color,
                )
                self.db.add(mastery)

        self.db.commit()
        return {"message": "掌握度已更新"}

    # ========== Get Map ==========

    def get_map(self, user_id: str, subject_id: str, time_range: Optional[str] = None) -> dict:
        uid = uuid.UUID(user_id)
        sid = uuid.UUID(subject_id)
        user = self._get_user(user_id)
        plan = self._get_plan(user)
        locked_depth = 1 if plan == "FREE" else None

        nodes = (
            self.db.query(KnowledgeNode)
            .filter_by(subject_id=sid)
            .order_by(KnowledgeNode.depth, KnowledgeNode.sort_order)
            .all()
        )

        # Determine time filter
        time_filter = None
        if time_range == "this_week":
            now = datetime.now(timezone.utc)
            # Start of this week (Monday)
            start_of_week = now - timedelta(days=now.weekday())
            time_filter = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        # Build mastery map for this user
        mastery_map = {}
        for node in nodes:
            if time_filter:
                # Filter answers by time range
                answers = (
                    self.db.query(Answer)
                    .join(Question, Answer.question_id == Question.id)
                    .filter(
                        Answer.user_id == uid,
                        Question.node_id == node.id,
                        Answer.answered_at >= time_filter,
                    )
                    .all()
                )
                total = len(answers)
                correct = sum(1 for a in answers if a.is_correct)
                rate = round(correct / total * 100, 2) if total > 0 else None
                color = self._compute_color(Decimal(str(rate)) if rate else None, total)
                mastery_map[node.id] = {
                    "mastery_rate": rate,
                    "color": color,
                    "wrong_count": total - correct,
                }
            else:
                mastery = self.db.query(NodeMastery).filter_by(
                    user_id=uid, node_id=node.id
                ).first()
                if mastery and mastery.total_count > 0:
                    rate = float(mastery.mastery_rate)
                    mastery_map[node.id] = {
                        "mastery_rate": rate,
                        "color": self._compute_color(Decimal(str(rate)), mastery.total_count),
                        "wrong_count": mastery.total_count - mastery.correct_count,
                    }
                else:
                    mastery_map[node.id] = {
                        "mastery_rate": None,
                        "color": "gray",
                        "wrong_count": 0,
                    }

        # Build tree
        tree = self._build_mastery_tree(nodes, mastery_map, locked_depth)
        return {"nodes": tree}

    def _build_mastery_tree(self, nodes, mastery_map, locked_depth=None):
        node_map = {}
        for n in nodes:
            m = mastery_map.get(n.id, {"mastery_rate": None, "color": "gray", "wrong_count": 0})
            is_locked = locked_depth is not None and n.depth > locked_depth

            node_map[n.id] = {
                "id": str(n.id),
                "name": n.name,
                "depth": n.depth,
                "mastery_rate": None if is_locked else m["mastery_rate"],
                "color": None if is_locked else m["color"],
                "wrong_count": 0 if is_locked else m["wrong_count"],
                "children": [],
                "locked": is_locked,
            }

        roots = []
        for n in nodes:
            d = node_map[n.id]
            if n.parent_id and n.parent_id in node_map:
                node_map[n.parent_id]["children"].append(d)
            else:
                roots.append(d)

        # Calculate parent mastery as weighted average of children
        self._calculate_parent_mastery(roots, locked_depth)

        return roots

    def _calculate_parent_mastery(self, nodes, locked_depth=None):
        for node in nodes:
            if node.get("locked"):
                continue
            self._calculate_parent_mastery(node["children"], locked_depth)
            children = node["children"]
            if children:
                child_rates = [c["mastery_rate"] for c in children
                               if c.get("mastery_rate") is not None and not c.get("locked")]
                if child_rates:
                    avg = sum(child_rates) / len(child_rates)
                    node["mastery_rate"] = round(avg, 2)
                    node["color"] = self._compute_color(
                        Decimal(str(node["mastery_rate"])), 1
                    )
                    # Sum wrong counts from children
                    node["wrong_count"] = sum(
                        c.get("wrong_count", 0) for c in children if not c.get("locked")
                    )

    # ========== Node Wrong Answers ==========

    def get_node_wrong_answers(self, user_id: str, node_id: str) -> dict:
        uid = uuid.UUID(user_id)
        nid = uuid.UUID(node_id)

        wrong_answers = (
            self.db.query(Answer, Question, Exam)
            .join(Question, Answer.question_id == Question.id)
            .join(Exam, Answer.exam_id == Exam.id)
            .filter(
                Answer.user_id == uid,
                Answer.is_correct == False,  # noqa: E712
                Question.node_id == nid,
            )
            .all()
        )

        result = []
        for answer, question, exam in wrong_answers:
            result.append({
                "question_id": str(question.id),
                "content": question.content[:120] if question.content else "",
                "student_answer": answer.selected_answer,
                "correct_answer": question.correct_answer,
                "difficulty": question.difficulty if hasattr(question.difficulty, '__str__') else str(question.difficulty),
                "exam_date": answer.answered_at.isoformat() if answer.answered_at else None,
                "source_type": question.source_type,
            })

        return {"wrong_answers": result}

    # ========== Export Markdown ==========

    def export_markdown(self, user_id: str, subject_id: str) -> str:
        uid = uuid.UUID(user_id)
        sid = uuid.UUID(subject_id)

        nodes = (
            self.db.query(KnowledgeNode)
            .filter_by(subject_id=sid)
            .order_by(KnowledgeNode.depth, KnowledgeNode.sort_order)
            .all()
        )

        # Get mastery data
        mastery_map = {}
        for node in nodes:
            mastery = self.db.query(NodeMastery).filter_by(
                user_id=uid, node_id=node.id
            ).first()
            if mastery and mastery.total_count > 0:
                mastery_map[node.id] = {
                    "rate": float(mastery.mastery_rate),
                    "color": mastery.color,
                    "wrong_count": mastery.total_count - mastery.correct_count,
                }
            else:
                mastery_map[node.id] = None

        lines = []
        for n in nodes:
            prefix = "#" * n.depth
            m = mastery_map.get(n.id)
            if m:
                emoji = {"green": "🟢", "orange": "🟡", "red": "🔴"}.get(m["color"], "⚪")
                wrong_info = f" — 錯題 {m['wrong_count']} 題" if m["wrong_count"] > 0 else ""
                lines.append(f"{prefix} {n.name} {emoji} ({m['rate']:.0f}%){wrong_info}")
            else:
                lines.append(f"{prefix} {n.name} ⚪ (未作答)")

        return "\n".join(lines)

    # ========== AI 學習建議（Feature 27 Rule 159）==========

    def get_suggestions(self, user_id: str, subject_id: Optional[str] = None) -> dict:
        """依錯題地圖紅色節點產出學習建議（紅色 = mastery_rate < 60）。

        排序：mastery_rate ASC（最低掌握度優先）。
        """
        uid = uuid.UUID(user_id)

        q = self.db.query(NodeMastery, KnowledgeNode).join(
            KnowledgeNode, NodeMastery.node_id == KnowledgeNode.id
        ).filter(NodeMastery.user_id == uid)

        if subject_id:
            q = q.filter(KnowledgeNode.subject_id == uuid.UUID(subject_id))

        rows = q.all()

        red_items = []
        for mastery, node in rows:
            if mastery.total_count and mastery.total_count > 0 and float(mastery.mastery_rate) < 60:
                red_items.append((mastery, node))

        red_items.sort(key=lambda pair: float(pair[0].mastery_rate))

        suggestions = []
        for mastery, node in red_items:
            rate = float(mastery.mastery_rate)
            if rate < 30:
                action, est = "deep_dive", 30
            elif rate < 45:
                action, est = "review", 20
            else:
                action, est = "quiz", 15
            suggestions.append({
                "target_node": {"id": str(node.id), "name": node.name},
                "current_rate": rate,
                "suggested_action": action,
                "estimated_time": est,
            })

        return {"suggestions": suggestions, "total": len(suggestions)}
