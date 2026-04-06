"""Then 考科知識樹應更新為匯入的結構 — Aggregate Then"""

import uuid

from behave import then

from app.models.knowledge_node import KnowledgeNode


@then('考科 "{subject_name}" 的知識樹應更新為匯入的結構')
def step_impl(context, subject_name):
    db = context.db_session

    subject_id_str = context.ids.get(f"subject_name_{subject_name}")
    assert subject_id_str, f"找不到考科 '{subject_name}'"
    subject_id = uuid.UUID(subject_id_str)

    nodes = db.query(KnowledgeNode).filter_by(subject_id=subject_id).all()
    assert len(nodes) > 0, \
        f"預期考科 '{subject_name}' 有知識節點，但未找到任何節點"


@then('根節點數量應為 {count:d}（{names}）')
def step_impl_root_count(context, count, names):
    db = context.db_session

    # Find subject from context
    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break
    assert subject_id, "找不到任何考科"

    root_nodes = db.query(KnowledgeNode).filter(
        KnowledgeNode.subject_id == subject_id,
        KnowledgeNode.depth == 1,
        KnowledgeNode.parent_id.is_(None),
    ).all()

    assert len(root_nodes) == count, \
        f"預期根節點數量為 {count}，實際為 {len(root_nodes)}"
