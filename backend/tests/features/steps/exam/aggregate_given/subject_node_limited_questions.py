"""Given 考科知識節點僅有 N 題考古題 — Aggregate Given"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
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

    # 記錄到 memo
    if "node_limited_questions" not in context.memo:
        context.memo["node_limited_questions"] = {}
    context.memo["node_limited_questions"][node_name] = count
