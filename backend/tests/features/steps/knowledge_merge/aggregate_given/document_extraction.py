"""Given 使用者上傳教材，系統萃取出知識節點 — Aggregate Given"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode


@given('使用者 "{email}" 上傳教材 "{doc_name}"，系統萃取出知識節點：')
def step_upload_document_extraction(context, email, doc_name):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id_str = context.memo.get("merge_subject_id")
    subject_id = uuid.UUID(subject_id_str) if subject_id_str else None

    incoming_nodes = []
    node_map = {}
    for row in context.table:
        name = row["節點名稱"]
        depth = int(row["層級"])
        parent_name = row["父節點"]
        source = row["來源"]

        incoming_nodes.append({
            "name": name,
            "depth": depth,
            "parent_name": parent_name if parent_name != "null" else None,
            "source_origin": source,
        })
        node_map[name] = {"name": name, "depth": depth}

    context.memo["incoming_nodes"] = incoming_nodes
    context.memo["incoming_doc_name"] = doc_name
    context.memo["incoming_uploader"] = email


@given('新上傳萃取出節點 "{name}"')
def step_incoming_node_alt(context, name):
    """Alias without '教材'."""
    if not hasattr(context, "memo"):
        context.memo = {}

    context.memo.setdefault("incoming_nodes", []).append({
        "name": name,
        "depth": 1,
        "parent_name": None,
        "source_origin": "document",
    })
    context.memo[f"incoming_{name}"] = {"name": name, "depth": 1}


@given('新上傳教材萃取出節點 "{name}"')
def step_incoming_node(context, name):
    if not hasattr(context, "memo"):
        context.memo = {}

    context.memo.setdefault("incoming_nodes", []).append({
        "name": name,
        "depth": 1,
        "parent_name": None,
        "source_origin": "document",
    })
    context.memo[f"incoming_{name}"] = {"name": name, "depth": 1}


@given('新上傳萃取出 depth={d:d} 節點 "{name}"')
def step_incoming_node_with_depth(context, d, name):
    if not hasattr(context, "memo"):
        context.memo = {}

    context.memo.setdefault("incoming_nodes", []).append({
        "name": name,
        "depth": d,
        "parent_name": None,
        "source_origin": "document",
    })
    context.memo[f"incoming_{name}"] = {"name": name, "depth": d}


@given('使用者 "{email}" 上傳 YouTube "{video_name}"，萃取出：')
def step_upload_youtube_extraction(context, email, video_name):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    incoming_nodes = []
    for row in context.table:
        name = row["節點名稱"]
        depth = int(row["層級"])
        source = row["來源"]

        incoming_nodes.append({
            "name": name,
            "depth": depth,
            "parent_name": None,
            "source_origin": source,
        })

    context.memo["incoming_nodes"] = incoming_nodes
    context.memo["incoming_doc_name"] = video_name
    context.memo["incoming_uploader"] = email
