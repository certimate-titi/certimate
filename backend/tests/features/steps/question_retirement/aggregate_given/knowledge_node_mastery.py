"""Given AI 題對應知識節點掌握度 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from behave import given
from app.models.exam import Exam, ExamStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.question import Question
from app.models.question_stat import QuestionStat
from app.models.resource import Resource
from app.repositories.subject_repository import SubjectRepository


@given('使用者 "{email}" 有 AI 題對應知識節點 "{node_name}"')
def step_impl(context, email, node_name):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name("證券商業務員")
    now = datetime.now(timezone.utc)

    # 建立 Resource（KnowledgeNode 需要 resource_id）
    resource = Resource(
        user_id=user_id,
        subject_id=subject.id,
        type="pdf",
        name="測試資源",
        status="COMPLETED",
    )
    db.add(resource)
    db.flush()

    # 建立 KnowledgeNode
    node = KnowledgeNode(
        resource_id=resource.id,
        name=node_name,
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

    # 建立 AI 題（關聯至 node）
    q = Question(
        exam_id=exam.id,
        node_id=node.id,
        question_number=1,
        content=f"AI 生成題目：{node_name} 相關",
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

    db.commit()
    context.memo["ai_question_ids"] = [str(q.id)]
    context.memo["ai_exam_id"] = str(exam.id)
    context.memo["ai_subject_id"] = str(subject.id)
    context.memo["current_question_id"] = str(q.id)
    context.memo["current_user_id"] = str(user_id)
    context.memo["current_node_id"] = str(node.id)
    context.memo["current_node_name"] = node_name


@given('該知識節點掌握度為 🔴（< 60%）')
def step_red_mastery(context):
    db = context.db_session
    user_id = uuid.UUID(context.memo["current_user_id"])
    node_id = uuid.UUID(context.memo["current_node_id"])

    mastery = NodeMastery(
        user_id=user_id,
        node_id=node_id,
        correct_count=3,
        total_count=10,
        mastery_rate=Decimal("30.00"),
        color="red",
    )
    db.add(mastery)
    db.commit()


@given('該知識節點於 {days:d} 天前轉為 🟢（≥ 80%）')
def step_green_mastery(context, days):
    db = context.db_session
    user_id = uuid.UUID(context.memo["current_user_id"])
    node_id = uuid.UUID(context.memo["current_node_id"])
    updated_at = datetime.now(timezone.utc) - timedelta(days=days)

    mastery = NodeMastery(
        user_id=user_id,
        node_id=node_id,
        correct_count=9,
        total_count=10,
        mastery_rate=Decimal("90.00"),
        color="green",
        updated_at=updated_at,
    )
    db.add(mastery)
    db.commit()


@given('該節點下所有 AI 題 SM-2 皆達第 {stage:d} 階段以上')
def step_all_sm2_stage(context, stage):
    db = context.db_session
    user_id = uuid.UUID(context.memo["current_user_id"])
    node_id = uuid.UUID(context.memo["current_node_id"])

    stat = db.query(QuestionStat).filter_by(
        user_id=user_id, node_id=node_id
    ).first()
    if not stat:
        stat = QuestionStat(
            user_id=user_id,
            node_id=node_id,
            success_count=stage,
            fail_count=0,
        )
        db.add(stat)
    else:
        stat.success_count = max(stat.success_count, stage)
    db.commit()
