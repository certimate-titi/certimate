"""Given 考科 "{subject_name}" 尚無知識樹 — Aggregate Given"""

from behave import given

from app.models.knowledge_node import KnowledgeNode


@given('考科 "{subject_name}" 尚無知識樹')
def step_impl(context, subject_name):
    db = context.db_session
    subject_id_str = context.ids.get(f"subject_name_{subject_name}")
    assert subject_id_str, f"找不到考科 '{subject_name}'"

    import uuid
    subject_id = uuid.UUID(subject_id_str)

    # Ensure no knowledge nodes exist for this subject
    count = db.query(KnowledgeNode).filter(
        KnowledgeNode.subject_id == subject_id
    ).count()
    assert count == 0, f"考科 '{subject_name}' 已有 {count} 個知識節點，應為空"
