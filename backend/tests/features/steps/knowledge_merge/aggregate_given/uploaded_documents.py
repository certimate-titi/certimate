"""Given 使用者已上傳教材 / 考科已有 N 個核心主題 — Aggregate Given.

Feature 29 §「六大主題上限」相關前置條件。

這些 Given 不執行真正的 AI 萃取（避免依賴 Gemini），
僅記錄輸入並（必要時）直接在 DB 建立 depth=1 / depth=2 節點，
模擬統一萃取已完成的狀態，供後續 When/Then 驗證契約。
"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode


def _ensure_merge_subject_id(context):
    """Ensure merge_subject_id is set; default to first subject in Background."""
    if not hasattr(context, "memo"):
        context.memo = {}
    if "merge_subject_id" in context.memo:
        return
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            context.memo["merge_subject_id"] = val
            return


@given('使用者 "{email}" 已上傳 {count:d} 份教材')
def step_uploaded_n_documents(context, email, count):
    """記錄使用者已上傳 N 份教材（不實際建 Resource，僅供 When 統一萃取參考）。"""
    _ensure_merge_subject_id(context)
    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo["uploaded_doc_count"] = count
    context.memo["uploader_email"] = email


@given('使用者 "{email}" 又上傳了 {count:d} 份新教材，涵盖 {topic_count:d} 個全新面向')
def step_uploaded_n_more_documents_legacy(context, email, count, topic_count):
    # Legacy spelling guard (full-width comma variant); behave uses the next one.
    context.memo["new_uploaded_doc_count"] = count
    context.memo["new_facet_count"] = topic_count
    context.memo["uploader_email"] = email


@given('使用者 "{email}" 又上傳了 {count:d} 份新教材，涵蓋 {topic_count:d} 個全新面向')
def step_uploaded_n_more_documents(context, email, count, topic_count):
    """記錄追加上傳的教材數與新面向數。

    新面向超過剩餘的核心主題額度時，依規格應該被合併到既有
    主題下或作為 depth=2 子節點新增（由 When 步驟模擬合併）。
    """
    _ensure_merge_subject_id(context)
    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo["new_uploaded_doc_count"] = count
    context.memo["new_facet_count"] = topic_count
    context.memo["uploader_email"] = email


@given('考科 "{subject_name}" 已有 {count:d} 個核心主題')
def step_subject_has_n_core_topics(context, subject_name, count):
    """在 DB 直接建立 N 個 depth=1 節點作為既有核心主題。"""
    db = context.db_session
    subject_id_str = context.ids.get(f"subject_name_{subject_name}")
    assert subject_id_str, f"找不到考科 '{subject_name}'"
    subject_id = uuid.UUID(subject_id_str)

    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo["merge_subject_id"] = str(subject_id)

    existing_count = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject_id, KnowledgeNode.depth == 1)
        .count()
    )

    to_create = count - existing_count
    created_names = []
    for i in range(to_create):
        idx = existing_count + i + 1
        name = f"核心主題{idx}"
        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=1,
            sort_order=idx,
            source_origin="ai_unified",
        )
        db.add(node)
        db.flush()
        created_names.append(name)
        context.ids[f"node_{name}"] = str(node.id)

    db.commit()
    context.memo.setdefault("core_topic_names", []).extend(created_names)
    context.memo["existing_core_topic_count"] = count


@given('考科 "{subject_name}" 已完成統一知識樹萃取，有 N 個核心主題（N <= {limit:d}）')
def step_unified_extraction_done_n_topics(context, subject_name, limit):
    """模擬統一萃取已完成的狀態：建立 N 個 depth=1 節點（N=4 為預設）。"""
    db = context.db_session
    subject_id_str = context.ids.get(f"subject_name_{subject_name}")
    assert subject_id_str, f"找不到考科 '{subject_name}'"
    subject_id = uuid.UUID(subject_id_str)

    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo["merge_subject_id"] = str(subject_id)

    # Choose a representative N within the limit
    n = min(4, limit)

    existing_depth1 = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject_id, KnowledgeNode.depth == 1)
        .count()
    )

    created_names = []
    for i in range(n - existing_depth1):
        idx = existing_depth1 + i + 1
        name = f"核心主題{idx}"
        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=1,
            sort_order=idx,
            source_origin="ai_unified",
        )
        db.add(node)
        db.flush()
        created_names.append(name)
        context.ids[f"node_{name}"] = str(node.id)

    db.commit()
    context.memo["expected_depth1_count"] = n
    context.memo.setdefault("core_topic_names", []).extend(created_names)
