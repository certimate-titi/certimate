"""Given 考科知識節點僅有 N 題考古題 — Aggregate Given"""

import uuid

from behave import given

from app.models.historical_exam import HistoricalExam
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.resource import Resource, ResourceStatus
from app.models.subject import Subject
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.repositories.subject_repository import SubjectRepository


@given('考科 "{subject_name}" 知識節點 "{node_name}" 僅有 {count:d} 題考古題')
def step_impl(context, subject_name, node_name, count):
    db = context.db_session
    subject_repo = SubjectRepository(db)
    node_repo = KnowledgeNodeRepository(db)

    subject = subject_repo.find_by_name(subject_name)
    if not subject:
        raise KeyError(f"找不到學科 '{subject_name}'，請先建立")

    # 建立資源（如果還沒有）
    resource_key = f"historical_resource_{subject_name}_{node_name}"
    if resource_key not in context.ids:
        system_user_id = None
        for key, val in context.ids.items():
            if "@" in key:
                system_user_id = uuid.UUID(val)
                break

        resource = Resource(
            user_id=system_user_id,
            subject_id=subject.id,
            name=f"{subject_name}_{node_name}_考古題",
            type="pdf",
            status=ResourceStatus.COMPLETED,
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)
        context.ids[resource_key] = str(resource.id)

    resource_id = uuid.UUID(context.ids[resource_key])

    # 建立知識節點
    node = KnowledgeNode(
        resource_id=resource_id,
        name=node_name,
        depth=1,
        sort_order=0,
        available_questions=count,
    )
    node_repo.save(node)
    context.ids[f"node_{node_name}"] = str(node.id)

    # 確保 subject 有 exam_subject_codes
    exam_code = "TEST_EXAM"
    subject_code = f"test_{uuid.uuid4().hex[:8]}"
    if not subject.exam_subject_codes:
        subject.exam_subject_codes = [f"{exam_code}:{subject_code}"]
        db.commit()
    else:
        parts = subject.exam_subject_codes[0].split(":", 1)
        if len(parts) == 2:
            exam_code, subject_code = parts[0], parts[1]

    # 建立 HistoricalExam 與 count 題考古題
    he_key = f"historical_exam_{subject_name}_{node_name}"
    if he_key not in context.ids:
        he = HistoricalExam(
            exam_code=exam_code,
            subject_code=subject_code,
            exam_name=f"{subject_name}_{node_name}_歷屆",
            subject_name=subject_name,
        )
        db.add(he)
        db.commit()
        db.refresh(he)
        context.ids[he_key] = str(he.id)
    he_id = uuid.UUID(context.ids[he_key])

    for i in range(count):
        q = Question(
            historical_exam_id=he_id,
            node_id=node.id,
            question_number=i + 1,
            content=f"{node_name} 考古題 #{i + 1}",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            source_type="historical",
            quality_flag="ok",
        )
        db.add(q)
    db.commit()

    # 記錄到 memo
    if "node_limited_questions" not in context.memo:
        context.memo["node_limited_questions"] = {}
    context.memo["node_limited_questions"][node_name] = count
