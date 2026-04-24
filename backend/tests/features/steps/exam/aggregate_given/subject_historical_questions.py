"""Given 考科有 N 題考古題 — Aggregate Given"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.historical_exam import HistoricalExam
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.resource import Resource, ResourceStatus
from app.models.subject import Subject, SubjectCategory
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.repositories.subject_repository import SubjectRepository, SubjectCategoryRepository


@given('考科 "{subject_name}" 有 {count:d} 題考古題')
def step_impl(context, subject_name, count):
    db = context.db_session
    subject_repo = SubjectRepository(db)
    cat_repo = SubjectCategoryRepository(db)
    node_repo = KnowledgeNodeRepository(db)

    # 取得或建立學科
    subject = subject_repo.find_by_name(subject_name)
    if not subject:
        if "exam_subject_cat" not in context.ids:
            cat = SubjectCategory(name="考試分類")
            cat_repo.save(cat)
            context.ids["exam_subject_cat"] = str(cat.id)
        cat_id = uuid.UUID(context.ids["exam_subject_cat"])
        subject = Subject(name=subject_name, category_id=cat_id)
        subject_repo.save(subject)

    context.ids[f"subject_{subject_name}"] = str(subject.id)

    # 更新 available_questions
    subject.available_questions = count
    db.commit()

    # 建立系統考古題資源
    system_user_id = None
    for key, val in context.ids.items():
        if "@" in key:
            system_user_id = uuid.UUID(val)
            break

    if system_user_id is None:
        system_user_id = uuid.uuid4()

    resource = Resource(
        user_id=system_user_id,
        subject_id=subject.id,
        name=f"{subject_name}_考古題",
        type="pdf",
        status=ResourceStatus.COMPLETED,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    context.ids[f"historical_resource_{subject_name}"] = str(resource.id)

    # 建立知識節點
    node = KnowledgeNode(
        resource_id=resource.id,
        name=f"{subject_name}_root",
        depth=0,
        sort_order=0,
        available_questions=count,
    )
    node_repo.save(node)
    context.ids[f"historical_node_{subject_name}"] = str(node.id)

    # 確保 subject 有 exam_subject_codes 以便 historical_only 抽題
    exam_code = "TEST_EXAM"
    subject_code = f"test_{uuid.uuid4().hex[:8]}"
    if not subject.exam_subject_codes:
        subject.exam_subject_codes = [f"{exam_code}:{subject_code}"]
    else:
        parts = subject.exam_subject_codes[0].split(":", 1)
        if len(parts) == 2:
            exam_code, subject_code = parts[0], parts[1]

    # 建立 HistoricalExam
    he = HistoricalExam(
        exam_code=exam_code,
        subject_code=subject_code,
        exam_name=f"{subject_name}_歷屆考題",
        subject_name=subject_name,
    )
    db.add(he)
    db.commit()
    db.refresh(he)
    context.ids[f"historical_exam_{subject_name}"] = str(he.id)

    # 建立 count 題考古題（附正確答案、綁定 historical_exam_id + root node）
    for i in range(count):
        q = Question(
            historical_exam_id=he.id,
            node_id=node.id,
            question_number=i + 1,
            content=f"{subject_name} 考古題 #{i + 1}",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            source_type="historical",
            quality_flag="ok",
            historical_source=he.exam_name,
        )
        db.add(q)
    db.commit()

    # 記錄考古題數量
    if "historical_count" not in context.memo:
        context.memo["historical_count"] = {}
    context.memo["historical_count"][subject_name] = count
