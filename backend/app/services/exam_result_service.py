"""Exam Result Service — 測驗結果業務邏輯。"""

import uuid

from sqlalchemy import func
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
                func.sum(func.cast(Answer.is_correct, sqlalchemy_int())).label("correct"),
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


def sqlalchemy_int():
    from sqlalchemy import Integer
    return Integer
