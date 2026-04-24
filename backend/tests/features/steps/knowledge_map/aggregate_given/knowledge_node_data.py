"""Given 系統中有包含歷史錯題、PDF 與 YouTube 的心智圖節點資料 — Aggregate Given"""

import uuid

from behave import given

from app.models.subject import SubjectCategory, Subject
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.knowledge_node import KnowledgeNode


@given('系統中有包含歷史錯題、PDF 與 YouTube 的心智圖節點資料')
def knowledge_node_data(context):
    db = context.db_session

    first_email = None
    for key in context.ids:
        if "@" in key:
            first_email = key
            break
    if not first_email:
        raise KeyError("需要至少一個使用者")

    user_id = uuid.UUID(context.ids[first_email])
    subject = (
        db.query(Subject).filter(Subject.name == "AWS SAA").first()
        or db.query(Subject).first()
    )
    if not subject:
        cat = db.query(SubjectCategory).first()
        if not cat:
            cat = SubjectCategory(name="IT")
            db.add(cat)
            db.flush()
        subject = Subject(name="AWS SAA", category_id=cat.id)
        db.add(subject)
        db.flush()
        context.ids["subject_AWS SAA"] = str(subject.id)

    # PDF resource with page-based nodes
    pdf_resource = Resource(
        user_id=user_id, subject_id=subject.id,
        name="AWS SAA 考試指南.pdf", type=ResourceType.PDF,
        status=ResourceStatus.COMPLETED,
    )
    db.add(pdf_resource)
    db.flush()
    context.ids["resource_pdf"] = str(pdf_resource.id)

    # YouTube resource with timestamp-based nodes
    yt_resource = Resource(
        user_id=user_id, subject_id=subject.id,
        name="AWS EC2 教學影片", type=ResourceType.YOUTUBE,
        youtube_url="https://youtube.com/watch?v=example",
        status=ResourceStatus.COMPLETED,
    )
    db.add(yt_resource)
    db.flush()
    context.ids["resource_youtube"] = str(yt_resource.id)

    # Root node
    root_node = KnowledgeNode(
        resource_id=pdf_resource.id, name="AWS SAA 核心概念",
        depth=0, sort_order=0,
    )
    db.add(root_node)
    db.flush()
    context.ids["node_root"] = str(root_node.id)

    # PDF child node (with page number)
    iam_node = KnowledgeNode(
        resource_id=pdf_resource.id, parent_id=root_node.id,
        name="IAM 身份管理", depth=1, sort_order=0,
        source_page_number=12, source_text="IAM 是 AWS 的身份與存取管理服務...",
    )
    db.add(iam_node)
    db.flush()
    context.ids["node_iam"] = str(iam_node.id)

    # YouTube child node (with timestamp)
    ec2_node = KnowledgeNode(
        resource_id=yt_resource.id, parent_id=root_node.id,
        name="EC2 運算邏輯", depth=1, sort_order=1,
        source_timestamp_seconds=512,
        source_text="EC2 是 AWS 的虛擬伺服器服務...",
    )
    db.add(ec2_node)
    db.flush()
    context.ids["node_ec2"] = str(ec2_node.id)
    context.ids["node_EC2 運算邏輯"] = str(ec2_node.id)

    # Subject-level unified tree nodes (resource_id=None) — required by
    # KnowledgeNavService.get_nodes_by_subject which filters resource_id IS NULL
    subject_root = KnowledgeNode(
        subject_id=subject.id, name="AWS SAA 知識樹",
        depth=0, sort_order=0,
    )
    db.add(subject_root)
    db.flush()

    s3_node = KnowledgeNode(
        subject_id=subject.id, parent_id=subject_root.id,
        name="AWS S3", depth=1, sort_order=0,
    )
    iam_unified = KnowledgeNode(
        subject_id=subject.id, parent_id=subject_root.id,
        name="IAM", depth=1, sort_order=1,
    )
    db.add_all([s3_node, iam_unified])

    db.commit()
