"""Given 科目有知識節點。"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode


@given('科目 "{subject_name}" 有以下知識節點：')
def step_impl(context, subject_name):
    db = context.db_session

    # 找到科目（由前面的 Given 建立）
    from app.models.subject import Subject
    subject = db.query(Subject).filter(Subject.name == subject_name).first()
    assert subject, f"找不到科目 {subject_name}"

    for row in context.table:
        node_name = row["節點名稱"]
        node_key = row["節點 ID"]
        parent_key = row.get("父節點 ID", "").strip()
        depth = int(row.get("深度", 0))

        parent_id = None
        if parent_key:
            parent_id = context.ids.get(f"node_{parent_key}")
            if parent_id:
                parent_id = uuid.UUID(parent_id)

        node = KnowledgeNode(
            name=node_name,
            subject_id=subject.id,
            depth=depth,
            parent_id=parent_id,
        )
        db.add(node)
        db.flush()

        context.ids[f"node_{node_key}"] = str(node.id)

    db.commit()
