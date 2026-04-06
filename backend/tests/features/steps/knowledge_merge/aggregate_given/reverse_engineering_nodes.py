"""Given 管理員已對考科完成考綱逆向工程，產出知識節點 — Aggregate Given"""

import uuid

from behave import given


@given('管理員已對考科 "{subject_name}" 完成考綱逆向工程，產出知識節點：')
def step_impl(context, subject_name):
    subject_id_str = context.ids[f"subject_name_{subject_name}"]
    subject_id = uuid.UUID(subject_id_str)

    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo["merge_subject_id"] = str(subject_id)

    # Only store as incoming nodes for the merge API — do NOT create in DB.
    # The merge pipeline will create them.
    incoming = []
    for row in context.table:
        name = row["節點名稱"]
        depth = int(row["層級"])
        parent_name = row["父節點"]
        source = row["來源"]

        incoming.append({
            "name": name,
            "depth": depth,
            "parent_name": parent_name if parent_name != "null" else None,
            "source_origin": source,
        })

    context.memo["incoming_nodes"] = incoming
