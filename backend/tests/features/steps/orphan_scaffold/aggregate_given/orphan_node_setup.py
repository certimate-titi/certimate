"""Given — orphan scaffold 測試環境建立（aggregate_given）.

建立：
- 已驗證學生帳號
- 有考古題的科目
- depth=2 orphan 節點（無 scaffold_node_link）
- 考古題（與節點名稱命中）
- AI_INFERRED 鷹架（cache 測試用）
"""

from __future__ import annotations

import json
import uuid

from behave import given

from app.models.historical_exam import HistoricalExam
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question, QuestionType, DifficultyLevel
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.scaffold_node_link import ScaffoldNodeLink
from app.models.scaffold_review_queue import ScaffoldReviewQueue
from app.models.subject import Subject, SubjectCategory
from app.models.user import User, UserStatus, UserRole, SubscriptionPlan, SubscriptionStatus
from app.services.auth_service import _hash_password


def _get_or_create_category(db) -> SubjectCategory:
    """取得或建立測試用科目分類."""
    cat = db.query(SubjectCategory).filter(
        SubjectCategory.name == "測試分類"
    ).first()
    if not cat:
        cat = SubjectCategory(
            id=uuid.uuid4(),
            name="測試分類",
            sort_order=999,
        )
        db.add(cat)
        db.flush()
    return cat


def _get_or_create_user(db, email: str, role: str = "user") -> User:
    """取得或建立測試用戶."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=_hash_password("TestPassword123!"),
            display_name=email.split("@")[0],
            status=UserStatus.ACTIVE,
            role=UserRole(role),
            subscription_plan=SubscriptionPlan.FREE,
            subscription_status=SubscriptionStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
    return user


@given('一位已驗證的學生帳號 "{email}"')
def step_student_account(context, email):
    db = context.db_session
    user = _get_or_create_user(db, email, role="user")
    db.commit()
    context.ids[email] = str(user.id)


@given('一個科目有 {count:d} 題考古題 "{subject_name}"')
def step_subject_with_questions(context, count, subject_name):
    db = context.db_session

    # 建立或取得科目
    subject = db.query(Subject).filter(Subject.name == subject_name).first()
    if not subject:
        cat = _get_or_create_category(db)
        subject = Subject(
            id=uuid.uuid4(),
            category_id=cat.id,
            name=subject_name,
            exam_subject_codes=[f"TEST001:{subject_name.replace(' ', '_')}"],
        )
        db.add(subject)
        db.flush()
    context.ids[subject_name] = str(subject.id)
    context.ids["current_subject_id"] = str(subject.id)

    # 建立 historical_exam
    he = db.query(HistoricalExam).filter(
        HistoricalExam.exam_code == "TEST001",
        HistoricalExam.subject_code == subject_name.replace(" ", "_"),
    ).first()
    if not he:
        he = HistoricalExam(
            id=uuid.uuid4(),
            exam_code="TEST001",
            subject_code=subject_name.replace(" ", "_"),
            exam_name=f"TEST 測試考試",
            subject_name=subject_name,
            total_questions=count,
            year=114,
        )
        db.add(he)
        db.flush()
    context.ids["current_he_id"] = str(he.id)

    # 建立考古題
    existing_count = (
        db.query(Question)
        .filter(Question.historical_exam_id == he.id)
        .count()
    )
    to_create = max(0, count - existing_count)
    for i in range(to_create):
        q = Question(
            id=uuid.uuid4(),
            historical_exam_id=he.id,
            question_number=existing_count + i + 1,
            type=QuestionType.SINGLE_CHOICE,
            difficulty=DifficultyLevel.MEDIUM,
            content=f"測試題目 {existing_count + i + 1}：關於考試科目的一般問題",
            option_a="選項A",
            option_b="選項B",
            option_c="選項C",
            option_d="選項D",
            correct_answer="A",
        )
        db.add(q)
    db.commit()


@given('科目下有一個 depth=2 的 orphan 節點 "{node_name}" 無任何 scaffold_node_link')
def step_orphan_node(context, node_name):
    db = context.db_session
    subject_id = uuid.UUID(context.ids["current_subject_id"])

    node = db.query(KnowledgeNode).filter(
        KnowledgeNode.name == node_name,
        KnowledgeNode.subject_id == subject_id,
        KnowledgeNode.depth == 2,
    ).first()
    if not node:
        node = KnowledgeNode(
            id=uuid.uuid4(),
            subject_id=subject_id,
            name=node_name,
            depth=2,
            sort_order=0,
            available_questions=0,
        )
        db.add(node)
        db.commit()
    context.ids[f"node_{node_name}"] = str(node.id)
    context.ids["current_node_id"] = str(node.id)
    context.ids["current_node_name"] = node_name


@given('節點 "{node_name}" 有 {count:d} 題對應考古題（精確命中）')
def step_node_with_exact_evidence(context, node_name, count):
    """建立與節點名稱精確命中的考古題."""
    db = context.db_session
    he_id = uuid.UUID(context.ids["current_he_id"])

    # 先刪除同節點的測試考古題（避免重複）
    existing = (
        db.query(Question)
        .filter(
            Question.historical_exam_id == he_id,
            Question.content.ilike(f"%{node_name}%"),
        )
        .all()
    )
    existing_ids = {q.id for q in existing}

    # 確保有足夠的精確命中題
    needed = max(0, count - len(existing))
    base_num = (
        db.query(Question)
        .filter(Question.historical_exam_id == he_id)
        .count()
    ) + 1

    for i in range(needed):
        q = Question(
            id=uuid.uuid4(),
            historical_exam_id=he_id,
            question_number=base_num + i,
            type=QuestionType.SINGLE_CHOICE,
            difficulty=DifficultyLevel.MEDIUM,
            content=f"{node_name}是指法律行為應符合誠信原則的具體應用，[考古題#{base_num + i}] 以下何者正確？",
            option_a="選項A正確",
            option_b="選項B錯誤",
            option_c="選項C錯誤",
            option_d="選項D錯誤",
            correct_answer="A",
        )
        db.add(q)
    db.commit()


@given('節點 "{node_name}" 只有 {count:d} 題對應考古題')
def step_node_with_few_evidence(context, node_name, count):
    """建立不足 3 題的考古題情境."""
    db = context.db_session
    he_id = uuid.UUID(context.ids["current_he_id"])

    # 移除超過 count 的命中題（若有）
    excess = (
        db.query(Question)
        .filter(
            Question.historical_exam_id == he_id,
            Question.content.ilike(f"%{node_name}%"),
        )
        .all()
    )
    for q in excess:
        db.delete(q)
    db.flush()

    # 建立精確 count 題
    base_num = (
        db.query(Question)
        .filter(Question.historical_exam_id == he_id)
        .count()
    ) + 1

    for i in range(count):
        q = Question(
            id=uuid.uuid4(),
            historical_exam_id=he_id,
            question_number=base_num + i,
            type=QuestionType.SINGLE_CHOICE,
            difficulty=DifficultyLevel.MEDIUM,
            content=f"{node_name}測試題 {base_num + i}：關於此節點的問題",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
        )
        db.add(q)
    db.commit()


@given('節點 "{node_name}" 已有 AI_INFERRED 鷹架')
def step_node_has_ai_scaffold(context, node_name):
    """建立已有 AI_INFERRED 鷹架的節點."""
    db = context.db_session
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    # 確認是否已有鷹架
    existing = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .filter(
            ScaffoldNodeLink.node_id == node_id,
            ResourceScaffold.is_orphan_fill.is_(True),
        )
        .first()
    )
    if existing:
        context.ids["current_scaffold_id"] = str(existing.id)
        return

    content = json.dumps({
        "definition": f"{node_name}是指法律行為應符合誠信原則的具體應用。[考古題#1]",
        "illustration": "例如甲向乙借款，雙方約定利率，甲不得主張利率過高而拒絕償還。（改編自 2024 年第 3 題）",
        "practice_question": {
            "stem": f"下列關於{node_name}的敘述，何者正確？",
            "options": ["A. 適用所有法律行為", "B. 僅適用契約", "C. 僅適用物權", "D. 不適用"],
            "answer": "A",
            "explanation": "因為法律行為均應遵守誠信原則，故 A 正確。",
            "difficulty": "T2",
        },
    }, ensure_ascii=False)

    scaffold = ResourceScaffold(
        id=uuid.uuid4(),
        resource_id=None,
        type=ResourceScaffoldType.CONCEPT_EXTRACT,
        content=content,
        template_code="K-ORPHAN-01",
        trust_level="AI_INFERRED",
        confidence_score=40,
        is_orphan_fill=True,
    )
    db.add(scaffold)
    db.flush()

    link = ScaffoldNodeLink(
        scaffold_id=scaffold.id,
        node_id=node_id,
        similarity=1.0,
        link_method="orphan_fill",
    )
    db.add(link)
    db.commit()
    context.ids["current_scaffold_id"] = str(scaffold.id)


@given('另外 {count:d} 個學生帳號 "{email2}" 和 "{email3}"')
def step_additional_users(context, count, email2, email3):
    db = context.db_session
    for email in [email2, email3]:
        user = _get_or_create_user(db, email)
        context.ids[email] = str(user.id)
    db.commit()


@given('"{email}" 已回報鷹架 "{reason_code}"')
def step_user_reported(context, email, reason_code):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    scaffold_id = uuid.UUID(context.ids["current_scaffold_id"])

    existing = db.query(ScaffoldReviewQueue).filter(
        ScaffoldReviewQueue.scaffold_id == scaffold_id,
        ScaffoldReviewQueue.reporter_user_id == user_id,
    ).first()
    if not existing:
        report = ScaffoldReviewQueue(
            scaffold_id=scaffold_id,
            reporter_user_id=user_id,
            reason_code=reason_code,
            note=None,
        )
        db.add(report)
        db.commit()


@given('學生 "{email}" 已回報過此鷹架')
def step_student_already_reported(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    scaffold_id = uuid.UUID(context.ids["current_scaffold_id"])

    existing = db.query(ScaffoldReviewQueue).filter(
        ScaffoldReviewQueue.scaffold_id == scaffold_id,
        ScaffoldReviewQueue.reporter_user_id == user_id,
    ).first()
    if not existing:
        report = ScaffoldReviewQueue(
            scaffold_id=scaffold_id,
            reporter_user_id=user_id,
            reason_code="definition_wrong",
            note=None,
        )
        db.add(report)
        db.commit()


@given('一位管理員帳號 "{email}"')
def step_admin_account(context, email):
    db = context.db_session
    user = _get_or_create_user(db, email, role="admin")
    db.commit()
    context.ids[email] = str(user.id)


@given('節點 "{node_name}" 已有 AI_INFERRED 鷹架被 3 位不同用戶回報')
def step_scaffold_with_three_reports(context, node_name):
    """建立已被 3 位不同用戶回報的鷹架."""
    db = context.db_session
    # 確保有鷹架
    step_node_has_ai_scaffold(context, node_name)
    scaffold_id = uuid.UUID(context.ids["current_scaffold_id"])

    reporter_emails = ["reporter_a@test.com", "reporter_b@test.com", "reporter_c@test.com"]
    for i, email in enumerate(reporter_emails):
        user = _get_or_create_user(db, email)
        context.ids[email] = str(user.id)
        existing = db.query(ScaffoldReviewQueue).filter(
            ScaffoldReviewQueue.scaffold_id == scaffold_id,
            ScaffoldReviewQueue.reporter_user_id == user.id,
        ).first()
        if not existing:
            report = ScaffoldReviewQueue(
                scaffold_id=scaffold_id,
                reporter_user_id=user.id,
                reason_code=["definition_wrong", "example_wrong", "unrelated"][i],
            )
            db.add(report)

    # 同時把 trust_level 改成 PENDING_REVIEW
    scaffold = db.query(ResourceScaffold).filter(
        ResourceScaffold.id == scaffold_id
    ).first()
    if scaffold:
        scaffold.trust_level = "PENDING_REVIEW"
    db.commit()
