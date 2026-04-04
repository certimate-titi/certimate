"""Given 考科有系統考古題資源及知識節點 — Aggregate Given"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceStatus
from app.models.subject import Subject
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.repositories.subject_repository import SubjectRepository


@given('考科 "{subject_name}" 有系統考古題資源，包含以下知識節點：')
def step_impl(context, subject_name):
    db = context.db_session
    subject_repo = SubjectRepository(db)
    node_repo = KnowledgeNodeRepository(db)

    subject = subject_repo.find_by_name(subject_name)
    if not subject:
        raise KeyError(f"找不到學科 '{subject_name}'，請先建立")

    # 建立系統考古題資源
    system_user_id = None
    for key, val in context.ids.items():
        if "@" in key:
            system_user_id = uuid.UUID(val)
            break

    resource = Resource(
        user_id=system_user_id,
        subject_id=subject.id,
        name=f"{subject_name}_系統考古題",
        type="pdf",
        status=ResourceStatus.COMPLETED,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    context.ids[f"system_resource_{subject_name}"] = str(resource.id)

    for row in context.table:
        node_name = row["節點名稱"]
        available = int(row["可出題數"])

        node = KnowledgeNode(
            resource_id=resource.id,
            name=node_name,
            depth=1,
            sort_order=0,
            available_questions=available,
        )
        node_repo.save(node)
        context.ids[f"node_{node_name}"] = str(node.id)
