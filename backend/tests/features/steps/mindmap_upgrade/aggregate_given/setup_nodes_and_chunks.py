"""Given — 建立 subject + knowledge_nodes + resource_chunks 組合 (mindmap upgrade)."""

from datetime import datetime, timezone
import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.resource import Resource, ResourceStatus, ResourceType
from app.models.resource_chunk import ResourceChunk
from app.models.subject import Subject, SubjectCategory
from app.models.user import SubscriptionPlan, User, UserRole, UserStatus


def _ensure_subject(db, subject_name: str) -> uuid.UUID:
    subj = db.query(Subject).filter(Subject.name == subject_name).first()
    if subj:
        return subj.id
    cat = db.query(SubjectCategory).first()
    if cat is None:
        cat = SubjectCategory(name="BDD Category")
        db.add(cat)
        db.flush()
    subj = Subject(name=subject_name, category_id=cat.id)
    db.add(subj)
    db.flush()
    return subj.id


def _ensure_user(db, context) -> uuid.UUID:
    # reuse the first learner user in context
    for key, uid in context.ids.items():
        if "@" in key and "learner" in key:
            return uuid.UUID(uid)
    # fallback: any user
    for key, uid in context.ids.items():
        if "@" in key:
            return uuid.UUID(uid)
    raise AssertionError("no user in context.ids")


def _ensure_resource(db, user_id, subject_id, name) -> uuid.UUID:
    r = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name=name,
        type=ResourceType.PDF,
        status=ResourceStatus.COMPLETED,
    )
    db.add(r)
    db.flush()
    return r.id


def _make_chunk(
    db, resource_id, node_id, index, content, dim=1024
) -> ResourceChunk:
    chunk = ResourceChunk(
        resource_id=resource_id,
        node_id=node_id,
        chunk_index=index,
        content=content,
        token_count=max(len(content) // 4, 1),
        embedding=[0.1] * dim,  # dummy vector
    )
    db.add(chunk)
    return chunk


@given('系統有一個科目 "{subject_name}" 含 {n:d} 個知識節點 "{n1}"、"{n2}"')
def step_impl_subject_two_nodes(context, subject_name, n, n1, n2):
    db = context.db_session
    sid = _ensure_subject(db, subject_name)
    user_id = _ensure_user(db, context)
    context.memo["subject_id"] = str(sid)
    context.memo["user_id"] = str(user_id)

    node_ids = {}
    for idx, nm in enumerate([n1, n2]):
        node = KnowledgeNode(
            subject_id=sid,
            name=nm,
            depth=1,
            sort_order=idx,
        )
        db.add(node)
        db.flush()
        node_ids[nm] = str(node.id)
    db.commit()
    context.memo["nodes"] = node_ids


@given('每個節點各關聯 {n:d} 個 resource_chunks')
def step_impl_chunks_per_node(context, n):
    db = context.db_session
    user_id = uuid.UUID(context.memo["user_id"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    resource_id = _ensure_resource(db, user_id, subject_id, "bdd-setup.pdf")
    context.memo["resource_id"] = str(resource_id)

    chunk_index = 0
    for node_name, node_id in context.memo.get("nodes", {}).items():
        for i in range(n):
            _make_chunk(
                db,
                resource_id,
                uuid.UUID(node_id),
                chunk_index,
                f"chunk for {node_name} #{i}",
            )
            chunk_index += 1
    db.commit()


@given('使用者 "{email}" 對 "{node_name}" 節點已標記為 "MASTERED"')
def step_impl_mark_mastered(context, email, node_name):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    node_id = uuid.UUID(context.memo["nodes"][node_name])

    existing = (
        db.query(NodeMastery)
        .filter(NodeMastery.user_id == user_id, NodeMastery.node_id == node_id)
        .first()
    )
    if existing is None:
        existing = NodeMastery(
            user_id=user_id,
            node_id=node_id,
            status="MASTERED",
            base_mastery=1.0,
        )
        db.add(existing)
    else:
        existing.status = "MASTERED"
        existing.base_mastery = 1.0
    db.commit()


@given('使用者 "{email}" 尚未有任何 mastery 紀錄')
def step_impl_no_mastery(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    db.query(NodeMastery).filter(NodeMastery.user_id == user_id).delete()
    db.commit()


@given('系統有一個科目 "{subject_name}" 含 {n:d} 個知識節點 "{n1}"')
def step_impl_subject_one_node(context, subject_name, n, n1):
    db = context.db_session
    sid = _ensure_subject(db, subject_name)
    user_id = _ensure_user(db, context)
    context.memo["subject_id"] = str(sid)
    context.memo["user_id"] = str(user_id)

    node = KnowledgeNode(
        subject_id=sid,
        name=n1,
        depth=1,
        sort_order=0,
    )
    db.add(node)
    db.flush()
    context.memo["nodes"] = {n1: str(node.id)}
    db.commit()


@given('該節點關聯 {n:d} 個 resource_chunks')
def step_impl_chunks_single_node(context, n):
    step_impl_chunks_per_node(context, n)


@given('系統建立一個新知識節點 "{node_name}"')
def step_impl_single_new_node(context, node_name):
    db = context.db_session
    sid = _ensure_subject(db, "BDD Test Subject")
    node = KnowledgeNode(subject_id=sid, name=node_name, depth=1, sort_order=0)
    db.add(node)
    db.commit()
    context.memo["single_node_id"] = str(node.id)


@given('系統有一個知識節點 "{node_name}" 關聯 {n:d} 個 resource_chunks')
def step_impl_node_with_chunks(context, node_name, n):
    db = context.db_session
    sid = _ensure_subject(db, "BDD Strength Test")
    user_id = _ensure_user(db, context)
    node = KnowledgeNode(subject_id=sid, name=node_name, depth=1, sort_order=0)
    db.add(node)
    db.flush()
    resource_id = _ensure_resource(db, user_id, sid, f"{node_name}-source.pdf")
    for i in range(n):
        _make_chunk(
            db, resource_id, node.id, i, f"{node_name} chunk {i}"
        )
    db.commit()
    context.memo["strength_node_id"] = str(node.id)
    context.memo["strength_node_name"] = node_name


@given('系統有一個知識節點 "{node_name}" 無任何 resource_chunks')
def step_impl_node_no_chunks(context, node_name):
    db = context.db_session
    sid = _ensure_subject(db, "BDD Strength Empty")
    node = KnowledgeNode(subject_id=sid, name=node_name, depth=1, sort_order=0)
    db.add(node)
    db.commit()
    context.memo["strength_node_id"] = str(node.id)
    context.memo["strength_node_name"] = node_name


@given('系統有一個資源 "{name}" 且已建立 {n:d} 個 chunks')
def step_impl_resource_with_chunks(context, name, n):
    db = context.db_session
    sid = _ensure_subject(db, "BDD Soft Delete")
    user_id = _ensure_user(db, context)
    resource_id = _ensure_resource(db, user_id, sid, name)
    for i in range(n):
        _make_chunk(db, resource_id, None, i, f"{name} chunk {i}")
    db.commit()
    context.memo["soft_del_resource_id"] = str(resource_id)


@given('GeminiCacheService 已初始化且無任何 entries')
def step_impl_init_cache(context):
    from app.services.gemini_cache_service import GeminiCacheService
    svc = GeminiCacheService()
    svc.invalidate_all()
    # Also reset stats
    import threading
    with svc._lock:  # type: ignore[attr-defined]
        svc._stats = {  # type: ignore[attr-defined]
            "hits": 0,
            "misses": 0,
            "creates": 0,
            "failures": 0,
            "cached_tokens_seen": 0,
        }
    context.memo["cache_svc"] = svc


@given('環境變數 GEMINI_EXPLICIT_CACHE_ENABLED 設為 "{value}"')
def step_impl_cache_env(context, value):
    import os
    os.environ["GEMINI_EXPLICIT_CACHE_ENABLED"] = value
    context.memo["_prev_cache_env"] = value
