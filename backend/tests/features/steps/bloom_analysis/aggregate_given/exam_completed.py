"""Given 完成一場含 Bloom 分類的測驗。"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.question import Question, QuestionType, DifficultyLevel, BloomCategory
from app.models.subject import Subject, SubjectCategory
from app.models.knowledge_node import KnowledgeNode


_BLOOM_MAP = {
    "remember": BloomCategory.REMEMBER,
    "understand": BloomCategory.UNDERSTAND,
    "apply": BloomCategory.APPLY,
    "analyze": BloomCategory.ANALYZE,
    "evaluate": BloomCategory.EVALUATE,
    "create": BloomCategory.CREATE,
}


@given('使用者 "{email}" 完成一場含 Bloom 分類的測驗')
def step_completed_exam(context, email):
    db = context.db_session
    user_id_str = context.ids.get(email)
    assert user_id_str, f"找不到使用者 {email}"
    user_id = uuid.UUID(user_id_str)

    # 取得或建立科目 + 節點
    subj = db.query(Subject).first()
    if not subj:
        cat = SubjectCategory(name="Bloom 結果分類")
        db.add(cat)
        db.flush()
        subj = Subject(name="Bloom 結果科目", category_id=cat.id)
        db.add(subj)
        db.flush()
    node = db.query(KnowledgeNode).filter_by(subject_id=subj.id).first()
    if not node:
        node = KnowledgeNode(
            subject_id=subj.id, name="結果節點",
            depth=1, available_questions=10,
        )
        db.add(node)
        db.flush()

    rows = list(context.table)
    now = datetime.now(timezone.utc)
    exam = Exam(
        user_id=user_id,
        subject_id=subj.id,
        status=ExamStatus.SUBMITTED,
        total_questions=len(rows),
        correct_count=sum(1 for r in rows if r["作答結果"] == "正確"),
        score=0,
        passing_score=60,
        duration_minutes=15,
        started_at=now,
        submitted_at=now,
    )
    db.add(exam)
    db.flush()
    exam.score = round(exam.correct_count / max(1, exam.total_questions) * 100)

    for idx, row in enumerate(rows, start=1):
        bloom_str = row["Bloom 分類"]
        is_correct = row["作答結果"] == "正確"
        q = Question(
            exam_id=exam.id,
            node_id=node.id,
            question_number=idx,
            type=QuestionType.SINGLE_CHOICE,
            difficulty=DifficultyLevel.MEDIUM,
            content=f"題 {idx}",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            bloom_category=_BLOOM_MAP[bloom_str],
            source_type="ai_generated",
            quality_flag="ok",
        )
        db.add(q)
        db.flush()
        a = Answer(
            exam_id=exam.id,
            user_id=user_id,
            question_id=q.id,
            selected_answer="A" if is_correct else "B",
            is_correct=is_correct,
        )
        db.add(a)

    db.commit()
    context.memo["completed_exam_id"] = str(exam.id)
    context.memo["completed_exam_email"] = email
    # 與既有 `使用者查看測驗結果` step 對齊（pomodoro/commands/pomodoro_actions.py）
    context.memo["current_user_email"] = email
    context.memo["current_exam_id"] = str(exam.id)
    context.ids[f"exam_id_{exam.id}"] = str(exam.id)
    context.memo["completed_exam_rows"] = [
        {"bloom": row["Bloom 分類"], "correct": row["作答結果"] == "正確"}
        for row in rows
    ]
