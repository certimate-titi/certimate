"""Historical exam markdown renderer — 動態將考古題題組輸出為 markdown。"""

import uuid
from sqlalchemy.orm import Session

from app.models.historical_exam import HistoricalExam
from app.models.question import Question
from app.models.subject import Subject


class HistoricalMarkdownService:
    """Historical Markdown Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    def list_for_subject(self, subject_id: str) -> list[dict]:
        """依 subject.exam_subject_codes 解析出該科目對應的 HistoricalExam 清單。

        Format: "EXAM_CODE:subject_code"，例：IPA114:114_ai_fundamentals_4th
        嚴守科目隔離 — 僅用該 subject 自己的 codes，禁用 parent fallback。
        """
        sid = uuid.UUID(subject_id)
        subject = self.db.query(Subject).filter_by(id=sid).first()
        if not subject or not subject.exam_subject_codes:
            return []

        pairs: list[tuple[str, str]] = []
        for code in subject.exam_subject_codes:
            if ":" in code:
                exam_code, subj_code = code.split(":", 1)
                pairs.append((exam_code, subj_code))

        if not pairs:
            return []

        from sqlalchemy import and_, or_
        clauses = [
            and_(HistoricalExam.exam_code == ec, HistoricalExam.subject_code == sc)
            for ec, sc in pairs
        ]
        exams = self.db.query(HistoricalExam).filter(or_(*clauses)).all()
        return [
            {
                "id": str(e.id),
                "exam_code": e.exam_code,
                "subject_code": e.subject_code,
                "name": e.exam_name or f"{e.exam_code} {e.subject_code}",
                "year": e.year,
                "total_questions": e.total_questions or 0,
            }
            for e in exams
        ]

    def render_markdown(self, historical_exam_id: str) -> dict:
        """Render 單場考古題為 markdown 字串。"""
        try:
            hid = uuid.UUID(historical_exam_id)
        except ValueError:
            return {"error": True, "status_code": 400, "message": "無效的考古題 ID"}

        exam = self.db.query(HistoricalExam).filter_by(id=hid).first()
        if not exam:
            return {"error": True, "status_code": 404, "message": "考古題不存在"}

        questions = (
            self.db.query(Question)
            .filter(Question.historical_exam_id == hid)
            .order_by(Question.question_number)
            .all()
        )

        lines: list[str] = [f"# {exam.exam_name or exam.exam_code}", ""]
        if exam.year:
            lines.append(f"> 年度：民國 {exam.year} 年")
        if exam.total_questions:
            lines.append(f"> 題目總數：{exam.total_questions}")
        lines.append("")

        for q in questions:
            lines.append(f"## 第 {q.question_number} 題")
            lines.append("")
            lines.append(q.content)
            lines.append("")
            for label, opt in [("A", q.option_a), ("B", q.option_b), ("C", q.option_c), ("D", q.option_d)]:
                if opt:
                    lines.append(f"- ({label}) {opt}")
            lines.append("")
            lines.append(f"**正解：{q.correct_answer}**")
            if q.explanation:
                lines.append("")
                lines.append(f"_解析：{q.explanation}_")
            lines.append("")

        return {
            "historical_exam_id": str(exam.id),
            "name": exam.exam_name,
            "content": "\n".join(lines),
            "question_count": len(questions),
        }
