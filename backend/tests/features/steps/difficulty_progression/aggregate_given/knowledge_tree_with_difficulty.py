"""Given 考科的知識樹如下（含難度基準）— Aggregate Given"""

import uuid

from behave import given
from decimal import Decimal

from app.models.knowledge_node import KnowledgeNode
from app.models.reverse_engineering_task import ReverseEngineeringTask


@given('考科 "{subject_name}" 的知識樹如下：')
def step_impl(context, subject_name):
    db = context.db_session

    subject_id_str = context.ids.get(f"subject_name_{subject_name}")
    if not subject_id_str:
        for key, val in context.ids.items():
            if key.startswith("subject_") and subject_name in key:
                subject_id_str = val
                break
    if not subject_id_str:
        raise KeyError(f"找不到考科 '{subject_name}'")

    subject_id = uuid.UUID(subject_id_str)

    # Find user for triggered_by
    admin_id = None
    for key, val in context.ids.items():
        if "@" in key:
            admin_id = uuid.UUID(val)
            break

    # Create completed task
    task = ReverseEngineeringTask(
        subject_id=subject_id,
        triggered_by=admin_id,
        status="COMPLETED",
        total_questions=50,
        node_count=len(context.table.rows),
        coverage_rate=Decimal("95.00"),
        max_depth=3,
        reliability="green",
    )
    db.add(task)
    db.flush()

    node_id_map = {}

    for row in context.table:
        table_id = row["節點 ID"]
        name = row["名稱"]
        depth = int(row["層級"])
        parent_table_id = row["父節點 ID"]
        difficulty = row.get("難度基準", "medium")

        parent_id = None
        if parent_table_id and parent_table_id.lower() != "null":
            parent_id = node_id_map.get(parent_table_id)

        node = KnowledgeNode(
            subject_id=subject_id,
            parent_id=parent_id,
            name=name,
            depth=depth,
            sort_order=int(table_id),
            exam_frequency="medium",
            source_origin="reverse_engineering",
        )
        db.add(node)
        db.flush()

        node_id_map[table_id] = node.id
        context.ids[f"node_{name}"] = str(node.id)
        context.ids[f"node_table_{table_id}"] = str(node.id)
        # Store difficulty mapping
        context.memo[f"node_difficulty_{name}"] = difficulty

    db.commit()
