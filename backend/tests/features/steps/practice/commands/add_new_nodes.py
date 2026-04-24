"""When 系統為考科新增 N 個新知識節點 — Epic 3 稀釋情境。"""

import uuid

from behave import when

from app.models.knowledge_node import KnowledgeNode
from app.services.organic_progress import OrganicProgressEngine


@when('系統為該考科新增 {n:d} 個新知識節點')
def step_add_new_nodes(context, n):
    db = context.db_session
    root_id = context.ids["dilution_root"]
    subject_id = context.ids["dilution_subject"]
    email = context.memo["dilution_email"]
    user_id = context.ids[email]

    existing_count = len(context.memo.get("dilution_existing_children", []))

    for i in range(n):
        node = KnowledgeNode(
            subject_id=uuid.UUID(subject_id),
            parent_id=uuid.UUID(root_id),
            name=f"新增節點 {i+1}",
            depth=1,
            sort_order=existing_count + i,
        )
        db.add(node)
    db.commit()

    engine = OrganicProgressEngine(db)
    engine.dilute_on_topology_change(
        user_id=user_id,
        root_node_id=root_id,
        new_topic_count=n,
    )
    db.commit()
