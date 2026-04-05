"""Mock Exam Service — 模擬機考業務邏輯。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.exam import Exam, ExamStatus
from app.models.answer import Answer
from app.models.question import Question


class MockExamService:

    def __init__(self, db: Session):
        self.db = db

    def start_exam(self, exam_id: str, user_id: str) -> dict:
        uid = uuid.UUID(user_id)
        exam = self.db.query(Exam).filter_by(id=uuid.UUID(exam_id)).first()

        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}

        if exam.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此測驗的權限"}

        if exam.status == ExamStatus.SUBMITTED:
            return {"error": True, "status_code": 400, "message": "測驗已提交，無法重新開始"}

        if exam.status == ExamStatus.IN_PROGRESS:
            return {"error": True, "status_code": 400, "message": "測驗已在進行中"}

        if exam.status != ExamStatus.READY:
            return {"error": True, "status_code": 400, "message": "測驗狀態不允許開始"}

        exam.status = ExamStatus.IN_PROGRESS
        exam.started_at = datetime.now(timezone.utc)
        self.db.commit()

        return {
            "error": False,
            "exam_id": str(exam.id),
            "status": "IN_PROGRESS",
            "started_at": exam.started_at.isoformat(),
        }

    def save_answer(self, exam_id: str, user_id: str, question_id: str,
                    selected_answer: str | None = None,
                    marked_for_review: bool | None = None) -> dict:
        uid = uuid.UUID(user_id)
        eid = uuid.UUID(exam_id)
        qid = uuid.UUID(question_id)

        exam = self.db.query(Exam).filter_by(id=eid).first()
        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}
        if exam.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此測驗的權限"}

        # Find or create answer
        answer = self.db.query(Answer).filter_by(
            exam_id=eid, question_id=qid, user_id=uid
        ).first()

        if not answer:
            answer = Answer(
                exam_id=eid,
                question_id=qid,
                user_id=uid,
            )
            self.db.add(answer)

        if selected_answer is not None:
            answer.selected_answer = selected_answer
            answer.answered_at = datetime.now(timezone.utc)

        if marked_for_review is not None:
            answer.marked_for_review = marked_for_review

        self.db.commit()

        return {
            "error": False,
            "question_id": str(qid),
            "selected_answer": answer.selected_answer,
            "marked_for_review": answer.marked_for_review,
        }

    def submit_exam(self, exam_id: str, user_id: str) -> dict:
        uid = uuid.UUID(user_id)
        exam = self.db.query(Exam).filter_by(id=uuid.UUID(exam_id)).first()

        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}
        if exam.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此測驗的權限"}
        if exam.status == ExamStatus.SUBMITTED:
            return {"error": True, "status_code": 400, "message": "測驗已提交，無法重複提交"}

        # Grade: compare each answer with correct answer
        questions = self.db.query(Question).filter_by(exam_id=exam.id).all()
        q_map = {str(q.id): q for q in questions}

        answers = self.db.query(Answer).filter_by(
            exam_id=exam.id, user_id=uid
        ).all()

        correct_count = 0
        for answer in answers:
            q = q_map.get(str(answer.question_id))
            if not q or not answer.selected_answer:
                answer.is_correct = False
                continue

            # Compare: correct_answer can be index ("0","1","2","3") or label ("A","B","C","D")
            correct = q.correct_answer
            selected = answer.selected_answer

            # Normalize both to index for comparison
            label_to_idx = {"A": "0", "B": "1", "C": "2", "D": "3"}
            correct_normalized = label_to_idx.get(correct.upper(), correct) if correct else ""
            selected_normalized = label_to_idx.get(selected.upper(), selected) if selected else ""

            answer.is_correct = (correct_normalized == selected_normalized)
            if answer.is_correct:
                correct_count += 1

        # Calculate score
        total = len(questions) or 1
        score = round((correct_count / total) * 100)

        exam.status = ExamStatus.SUBMITTED
        exam.submitted_at = datetime.now(timezone.utc)
        exam.score = score
        exam.correct_count = correct_count
        self.db.commit()

        return {
            "error": False,
            "exam_id": str(exam.id),
            "status": "SUBMITTED",
            "score": score,
            "correct_count": correct_count,
            "total_questions": total,
        }

    def resume_exam(self, exam_id: str, user_id: str) -> dict:
        uid = uuid.UUID(user_id)
        exam = self.db.query(Exam).filter_by(id=uuid.UUID(exam_id)).first()

        if not exam:
            return {"error": True, "status_code": 404, "message": "測驗不存在"}
        if exam.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此測驗的權限"}

        # Auto-start if READY
        if exam.status == ExamStatus.READY:
            exam.status = ExamStatus.IN_PROGRESS
            exam.started_at = datetime.now(timezone.utc)
            self.db.commit()

        # Get questions
        from app.models.question import Question
        questions = self.db.query(Question).filter_by(
            exam_id=exam.id
        ).order_by(Question.question_number).all()

        # Get saved answers
        answers = self.db.query(Answer).filter_by(
            exam_id=exam.id, user_id=uid
        ).all()

        return {
            "error": False,
            "exam_id": str(exam.id),
            "exam": {
                "id": str(exam.id),
                "title": getattr(exam, 'title', None) or "模擬測驗",
                "status": exam.status.value if hasattr(exam.status, 'value') else exam.status,
                "total_questions": exam.total_questions,
                "duration_minutes": exam.duration_minutes or max(15, int((exam.total_questions or 10) * 1.5)),
            },
            "status": exam.status.value if hasattr(exam.status, 'value') else exam.status,
            "questions": [
                {
                    "id": str(q.id),
                    "content": q.content,
                    "options": [
                        {"label": "A", "text": q.option_a or ""},
                        {"label": "B", "text": q.option_b or ""},
                        {"label": "C", "text": q.option_c or ""},
                        {"label": "D", "text": q.option_d or ""},
                    ],
                    "type": q.type.value if hasattr(q.type, 'value') else (q.type or "single_choice"),
                    "questionNumber": q.question_number,
                }
                for q in questions
            ],
            "answers": [
                {
                    "question_id": str(a.question_id),
                    "selected_answer": a.selected_answer,
                    "marked_for_review": a.marked_for_review,
                }
                for a in answers
            ],
        }
