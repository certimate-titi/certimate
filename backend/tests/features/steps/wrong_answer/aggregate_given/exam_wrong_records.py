"""Given 系統中有以下測驗與錯題記錄 / 測驗 N 包含以下錯題 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.subject import SubjectCategory, Subject
from app.models.question import Question, QuestionType
from app.models.answer import Answer
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope
from app.repositories.exam_repository import ExamRepository


# Map question content → explanation (tip) for test data.
# These must match the feature file expectations.
_TIP_MAP = {
    "S3 的版本控制功能預設為何？": "S3 版本控制預設為停用狀態。",
    "IAM Policy 的評估順序為何？": "IAM Policy 預設為拒絕，明確允許優先於預設拒絕。",
    "EC2 Auto Scaling 的觸發條件為何？": "Auto Scaling 可透過 CloudWatch Alarm 設定觸發條件。",
}


def _generate_tip(content: str, node_name: str) -> str:
    """Generate a tip/explanation for a question based on its content."""
    return _TIP_MAP.get(content, f"{node_name} 相關概念說明。")


@given('系統中有以下測驗與錯題記錄：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        exam_id_int = int(row["測驗 ID"])
        user_id_key = row["使用者 ID"].strip()
        status_raw = row["狀態"].strip()
        subject_name = row["科目"]

        user_uuid = uuid.UUID(context.ids[user_id_key])

        # Create subject if not exists
        subj_key = f"subject_{subject_name}"
        if subj_key not in context.ids:
            if "default_cat" not in context.ids:
                cat = SubjectCategory(name="default_cat")
                db.add(cat)
                db.flush()
                context.ids["default_cat"] = str(cat.id)
            cat_id = uuid.UUID(context.ids["default_cat"])
            subj = Subject(name=subject_name, category_id=cat_id)
            db.add(subj)
            db.flush()
            context.ids[subj_key] = str(subj.id)
            context.ids["default_subject"] = str(subj.id)

        subject_id = uuid.UUID(context.ids[subj_key])

        status_map = {
            "SUBMITTED": ExamStatus.SUBMITTED,
            "IN_PROGRESS": ExamStatus.IN_PROGRESS,
        }

        exam = Exam(
            id=uuid.UUID(int=exam_id_int),
            user_id=user_uuid,
            subject_id=subject_id,
            status=status_map.get(status_raw, ExamStatus.SUBMITTED),
            total_questions=10,
            duration_minutes=60,
            submitted_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
        )
        db.add(exam)
        db.flush()
        context.ids[f"exam_{exam_id_int}"] = str(exam.id)
        context.memo[f"exam_{exam_id_int}_subject"] = subject_name

    db.commit()


@given('測驗 {exam_id:d} 包含以下錯題：')
def step_impl_wrong(context, exam_id):
    db = context.db_session
    exam_uuid = uuid.UUID(int=exam_id)

    from app.models.exam import Exam
    exam = db.query(Exam).filter_by(id=exam_uuid).first()

    # Create resource if needed
    if "default_resource" not in context.ids:
        res = Resource(
            user_id=exam.user_id,
            subject_id=exam.subject_id,
            name="test_resource.pdf",
            type=ResourceType.PDF,
            status=ResourceStatus.COMPLETED,
            scope=ResourceScope.PERSONAL,
        )
        db.add(res)
        db.flush()
        context.ids["default_resource"] = str(res.id)

    resource_id = uuid.UUID(context.ids["default_resource"])

    for row in context.table:
        q_id_int = int(row["題目 ID"])
        content = row["題目內容"]
        correct_answer = row["正確答案"]
        user_selected = row["使用者選擇"]
        node_name = row["知識節點"]

        # Create or get node
        node_key = f"node_{node_name}"
        if node_key not in context.ids:
            node = KnowledgeNode(
                resource_id=resource_id,
                name=node_name,
                depth=1,
                sort_order=0,
            )
            db.add(node)
            db.flush()
            context.ids[node_key] = str(node.id)

        node_id = uuid.UUID(context.ids[node_key])

        q = Question(
            id=uuid.UUID(int=q_id_int),
            exam_id=exam_uuid,
            node_id=node_id,
            question_number=q_id_int,
            type=QuestionType.SINGLE_CHOICE,
            content=content,
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer=correct_answer,
            explanation=_generate_tip(content, node_name),
        )
        db.add(q)
        db.flush()

        answer = Answer(
            exam_id=exam_uuid,
            question_id=q.id,
            user_id=exam.user_id,
            selected_answer=user_selected,
            is_correct=False,
        )
        db.add(answer)

    db.commit()
