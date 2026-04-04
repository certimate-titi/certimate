"""Given 使用者有一題 AI 題在錯題本中 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.resource import Resource
from app.repositories.subject_repository import SubjectRepository


@given('使用者 "{email}" 有一題 AI 題在錯題本中')
def step_impl(context, email):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name("證券商業務員")
    now = datetime.now(timezone.utc)

    # 建立 Resource + KnowledgeNode（SM-2 需要 node_id）
    resource = Resource(
        user_id=user_id,
        subject_id=subject.id,
        type="pdf",
        name="錯題本測試資源",
        status="COMPLETED",
    )
    db.add(resource)
    db.flush()

    node = KnowledgeNode(
        resource_id=resource.id,
        name="錯題本測試節點",
        depth=0,
        sort_order=0,
    )
    db.add(node)
    db.flush()

    # 建立 Exam
    exam = Exam(
        user_id=user_id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED,
        total_questions=1,
    )
    db.add(exam)
    db.flush()

    # 建立 AI 題（掛上 node_id）
    q = Question(
        exam_id=exam.id,
        node_id=node.id,
        question_number=1,
        content="AI 生成題目：錯題本測試",
        option_a="選項 A",
        option_b="選項 B",
        option_c="選項 C",
        option_d="選項 D",
        correct_answer="A",
        source_type="ai_generated",
        quality_flag="ok",
        expires_at=now + timedelta(days=7),
    )
    db.add(q)
    db.flush()

    # 建立錯誤答案（加入錯題本）
    answer = Answer(
        exam_id=exam.id,
        question_id=q.id,
        user_id=user_id,
        selected_answer="B",
        is_correct=False,
        confidence="medium",
        answered_at=now,
    )
    db.add(answer)
    db.commit()

    context.memo["ai_question_ids"] = [str(q.id)]
    context.memo["ai_exam_id"] = str(exam.id)
    context.memo["ai_subject_id"] = str(subject.id)
    context.memo["current_question_id"] = str(q.id)
    context.memo["current_user_id"] = str(user_id)
    context.memo["current_node_id"] = str(node.id)
