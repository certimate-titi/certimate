"""Exam Result Service — 測驗結果業務邏輯。"""

import uuid
from collections import Counter

from sqlalchemy import func, Integer as SAInteger
from sqlalchemy.orm import Session

from app.models.exam import Exam, ExamStatus
from app.models.answer import Answer
from app.models.question import Question
from app.models.knowledge_node import KnowledgeNode


class ExamResultService:

    def __init__(self, db: Session):
        self.db = db

    def get_result(self, exam_id: str, user_id: str) -> dict:
        uid = uuid.UUID(user_id)
        exam = self.db.query(Exam).filter_by(id=uuid.UUID(exam_id)).first()

        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        if exam.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此測驗結果的權限"}

        if exam.status != ExamStatus.SUBMITTED:
            return {"error": True, "status_code": 400, "message": "測驗尚未提交，無法查看結果"}

        score = exam.score or 0
        passing_score = exam.passing_score or 0
        pass_status = "通過" if score >= passing_score else "未達門檻"

        # Find previous exam for comparison
        comparison = self._get_comparison(exam, uid)

        # Build user_answers from answers + questions
        questions = self.db.query(Question).filter_by(exam_id=exam.id).order_by(
            Question.question_number
        ).all()
        answers = self.db.query(Answer).filter_by(
            exam_id=exam.id, user_id=uid
        ).all()
        answer_map = {str(a.question_id): a for a in answers}

        user_answers = []
        for q in questions:
            a = answer_map.get(str(q.id))
            user_answers.append({
                "questionId": str(q.id),
                "questionNumber": q.question_number,
                "userChoice": a.selected_answer if a else None,
                "isCorrect": a.is_correct if a else False,
                "correctAnswer": q.correct_answer,
                "content": q.content,
                "optionA": q.option_a,
                "optionB": q.option_b,
                "optionC": q.option_c,
                "optionD": q.option_d,
                "explanation": q.explanation or "",
                "difficulty": getattr(q, 'difficulty', None),
                "bloomCategory": getattr(q, 'bloom_category', None),
                "reliability": "green" if getattr(q, 'historical_source', None) else "yellow",
            })

        time_spent = 0
        if exam.started_at and exam.submitted_at:
            time_spent = int((exam.submitted_at - exam.started_at).total_seconds())

        # Generate AI summary (cached in DB)
        ai_summary = self._get_or_generate_ai_summary(exam, questions, answer_map)

        # Generate domain analysis from knowledge nodes
        domain_analysis = self._build_domain_analysis(exam.id, answers)

        result = {
            "error": False,
            "exam_id": str(exam.id),
            "score": str(score),
            "pass_status": pass_status,
            "passing_score": str(passing_score),
            "correct_count": exam.correct_count,
            "total_questions": exam.total_questions,
            "time_spent_seconds": time_spent,
            "user_answers": user_answers,
            "ai_summary": ai_summary,
            "domain_analysis": domain_analysis,
            "questions": [
                {
                    "id": str(q.id),
                    "questionNumber": q.question_number,
                    "content": q.content,
                    "optionA": q.option_a,
                    "optionB": q.option_b,
                    "optionC": q.option_c,
                    "optionD": q.option_d,
                    "correctAnswer": q.correct_answer,
                    "explanation": q.explanation or "",
                }
                for q in questions
            ],
        }

        if comparison:
            result["comparison"] = comparison

        return result

    def _get_or_generate_ai_summary(self, exam, questions, answer_map) -> str:
        """Generate and cache AI analysis summary based on exam performance."""
        if exam.ai_summary:
            return exam.ai_summary

        total = len(questions)
        if total == 0:
            return ""

        correct = sum(
            1 for q in questions
            if answer_map.get(str(q.id)) and answer_map[str(q.id)].is_correct
        )
        rate = round(correct / total * 100)

        # Analyze by difficulty
        diff_stats: dict[str, list[int]] = {}
        bloom_stats: dict[str, list[int]] = {}
        for q in questions:
            d = getattr(q, 'difficulty', 'medium') or 'medium'
            b = getattr(q, 'bloom_category', 'remember') or 'remember'
            a = answer_map.get(str(q.id))
            is_correct = 1 if (a and a.is_correct) else 0

            diff_stats.setdefault(d, [0, 0])
            diff_stats[d][0] += is_correct
            diff_stats[d][1] += 1

            bloom_stats.setdefault(b, [0, 0])
            bloom_stats[b][0] += is_correct
            bloom_stats[b][1] += 1

        diff_labels = {"easy": "基礎題", "medium": "中等題", "hard": "進階題"}
        bloom_labels = {
            "remember": "記憶", "understand": "理解", "apply": "應用",
            "analyze": "分析", "evaluate": "評鑑", "create": "創造",
        }

        # Build summary parts
        parts = []

        # Overall performance
        if rate >= 90:
            parts.append(f"整體表現優異，答對率 {rate}%，展現了紮實的知識掌握度。")
        elif rate >= 70:
            parts.append(f"整體表現不錯，答對率 {rate}%，大部分知識點已掌握。")
        elif rate >= 50:
            parts.append(f"答對率 {rate}%，部分知識點需要加強，建議針對錯題進行複習。")
        else:
            parts.append(f"答對率 {rate}%，建議重新複習核心概念，並透過錯題本進行針對性練習。")

        # Difficulty analysis
        weak_diffs = []
        strong_diffs = []
        for d, (c, t) in diff_stats.items():
            r = round(c / t * 100) if t > 0 else 0
            label = diff_labels.get(d, d)
            if r < 50 and t >= 2:
                weak_diffs.append(f"{label}（{r}%）")
            elif r >= 80 and t >= 2:
                strong_diffs.append(f"{label}（{r}%）")

        if weak_diffs:
            parts.append(f"在{', '.join(weak_diffs)}的表現較弱，建議加強練習。")
        if strong_diffs:
            parts.append(f"在{', '.join(strong_diffs)}表現出色，繼續保持！")

        # Bloom taxonomy analysis
        weak_blooms = []
        for b, (c, t) in bloom_stats.items():
            r = round(c / t * 100) if t > 0 else 0
            label = bloom_labels.get(b, b)
            if r < 50 and t >= 2:
                weak_blooms.append(label)

        if weak_blooms:
            parts.append(f"在「{', '.join(weak_blooms)}」層次的題目需要多加練習，建議搭配錯題本深入理解。")

        summary = " ".join(parts)

        # Cache to DB
        exam.ai_summary = summary
        self.db.commit()

        return summary

    def _build_domain_analysis(self, exam_id, answers) -> list:
        """Build domain (knowledge node) analysis for the exam."""
        if not answers:
            return []

        results = (
            self.db.query(
                KnowledgeNode.name,
                func.sum(func.cast(Answer.is_correct, SAInteger)).label("correct"),
                func.count(Answer.id).label("total"),
            )
            .join(Question, Question.id == Answer.question_id)
            .join(KnowledgeNode, KnowledgeNode.id == Question.node_id)
            .filter(Answer.exam_id == exam_id)
            .group_by(KnowledgeNode.name)
            .all()
        )

        domain_list = []
        for name, correct, total in results:
            pct = round(correct / total * 100) if total > 0 else 0
            domain_list.append({
                "domain": name,
                "correct": correct,
                "total": total,
                "percentage": pct,
            })

        # Sort: weakest first
        domain_list.sort(key=lambda x: x["percentage"])
        return domain_list

    def _get_comparison(self, current_exam: Exam, user_id: uuid.UUID) -> str | None:
        # Find previous submitted exam (before current one)
        previous = self.db.query(Exam).filter(
            Exam.user_id == user_id,
            Exam.status == ExamStatus.SUBMITTED,
            Exam.id != current_exam.id,
            Exam.submitted_at < current_exam.submitted_at,
        ).order_by(Exam.submitted_at.desc()).first()

        if not previous or previous.score is None:
            return None

        diff = (current_exam.score or 0) - (previous.score or 0)
        if diff > 0:
            return f"+{diff} 分進步"
        elif diff < 0:
            return f"{diff} 分退步"
        else:
            return "持平"

    def get_node_analysis(self, exam_id: str, user_id: str) -> dict:
        uid = uuid.UUID(user_id)
        exam = self.db.query(Exam).filter_by(id=uuid.UUID(exam_id)).first()

        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        if exam.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此測驗結果的權限"}

        # Aggregate by knowledge node
        results = (
            self.db.query(
                KnowledgeNode.name,
                func.sum(func.cast(Answer.is_correct, SAInteger)).label("correct"),
                func.count(Answer.id).label("total"),
            )
            .join(Question, Question.id == Answer.question_id)
            .join(KnowledgeNode, KnowledgeNode.id == Question.node_id)
            .filter(Answer.exam_id == exam.id)
            .group_by(KnowledgeNode.name)
            .all()
        )

        nodes = []
        for name, correct, total in results:
            rate = round(correct / total * 100) if total > 0 else 0
            color = "綠色" if rate >= 60 else "紅色"
            nodes.append({
                "name": name,
                "correct": correct,
                "total": total,
                "accuracy_rate": f"{rate}%",
                "color": color,
            })

        return {"error": False, "nodes": nodes}
