"""Completion Framework — Aggregate Given steps.

建立測試所需的 DB 實體：科目、知識節點、NodeMastery、LearningJourney。

step pattern 前綴統一用「完成度測試」或「完成度用戶」，避免與其他子領域衝突。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from behave import given

from app.models.subject import Subject, SubjectCategory
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.learning_journey import LearningJourney


def _get_or_create_category(db) -> SubjectCategory:
    cat = db.query(SubjectCategory).first()
    if not cat:
        cat = SubjectCategory(name="測試分類", sort_order=0)
        db.add(cat)
        db.flush()
    return cat


def _get_subject_by_name(db, context, subject_name: str) -> Subject | None:
    """從 context.ids 取得 subject，或由 DB 查找。"""
    key = f"completion_subject_{subject_name}"
    sid_str = context.ids.get(key)
    if sid_str:
        return db.query(Subject).filter_by(id=uuid.UUID(sid_str)).first()
    return db.query(Subject).filter_by(name=subject_name).first()


def _create_subject(db, context, subject_name: str, user_id: uuid.UUID) -> Subject:
    """建立或取得 personal subject。"""
    existing = (
        db.query(Subject)
        .filter_by(name=subject_name, owner_user_id=user_id)
        .first()
    )
    if existing:
        context.ids[f"completion_subject_{subject_name}"] = str(existing.id)
        return existing

    cat = _get_or_create_category(db)
    subj = Subject(
        name=subject_name,
        category_id=cat.id,
        owner_user_id=user_id,
        scope="personal",
    )
    db.add(subj)
    db.flush()
    context.ids[f"completion_subject_{subject_name}"] = str(subj.id)
    return subj


def _create_nodes(
    db, context, subject: Subject, subject_name: str, freqs: list[int]
) -> list[str]:
    """為科目建立 depth=2 節點，清除既有節點。"""
    # 清除該科目既有節點（確保測試隔離）
    db.query(KnowledgeNode).filter_by(subject_id=subject.id).delete()
    db.flush()

    node_ids = []
    for i, freq in enumerate(freqs):
        node = KnowledgeNode(
            subject_id=subject.id,
            name=f"{subject_name}_node_{i+1}",
            depth=2,
            sort_order=i,
            available_questions=freq,
        )
        db.add(node)
        db.flush()
        node_ids.append(str(node.id))

    context.ids[f"completion_nodes_{subject_name}"] = node_ids
    return node_ids


# ─── 科目 + 節點建立 ──────────────────────────────────────────────────────

@given('完成度測試科目 "{subject_name}" 屬於用戶 "{email}" 有 {count:d} 個頻率為 "{freqs}" 的節點')
def step_subject_with_nodes(context, subject_name, email, count, freqs):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    subj = _create_subject(db, context, subject_name, user_id)

    freq_list = [int(f.strip()) for f in freqs.split(",")]
    assert len(freq_list) == count, f"頻率數量 {len(freq_list)} != {count}"
    _create_nodes(db, context, subj, subject_name, freq_list)
    db.commit()


@given('完成度測試科目 "{subject_name}" 屬於用戶 "{email}" 無節點')
def step_subject_no_nodes(context, subject_name, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    subj = _create_subject(db, context, subject_name, user_id)
    db.query(KnowledgeNode).filter_by(subject_id=subj.id).delete()
    db.commit()


@given('完成度測試科目 "{subject_name}" 額外新增 {count:d} 個頻率 "{freq}" 的未覆蓋節點')
def step_extra_uncovered_nodes(context, subject_name, count, freq):
    db = context.db_session
    subj = _get_subject_by_name(db, context, subject_name)
    assert subj is not None, f"找不到科目 {subject_name}"

    node_ids = context.ids.get(f"completion_nodes_{subject_name}", [])
    for i in range(count):
        node = KnowledgeNode(
            subject_id=subj.id,
            name=f"{subject_name}_extra_{i+1}",
            depth=2,
            sort_order=100 + i,
            available_questions=int(freq),
        )
        db.add(node)
        db.flush()
        node_ids.append(str(node.id))

    context.ids[f"completion_nodes_{subject_name}"] = node_ids
    db.commit()


# ─── NodeMastery 建立 ────────────────────────────────────────────────────

@given('用戶 "{email}" 在科目 "{subject_name}" 無任何 mastery 紀錄')
def step_no_mastery(context, email, subject_name):
    """確認無 mastery 紀錄（default state，無需動作）。"""
    pass


@given('完成度用戶 "{email}" 第 {n:d} 個節點 mastery "{mastery_val}" SM2間隔 "{interval}" 天')
def step_mastery_nth_node(context, email, n, mastery_val, interval):
    """為 CompletionSubjectA 的第 n 個節點建立 NodeMastery。"""
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    # 找出最近建立的 completion subject 節點
    node_ids = _find_last_subject_nodes(context)
    assert len(node_ids) >= n, f"節點數量不足 {n}"

    node_id = uuid.UUID(node_ids[n - 1])
    _create_mastery(db, user_id, node_id, float(mastery_val), int(interval))
    db.commit()


@given('完成度用戶 "{email}" 節點 mastery "{mastery_val}" 來源 "{source}"')
def step_mastery_ai_inferred(context, email, mastery_val, source):
    """建立 mastery，設定 trust_level / status。"""
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    node_ids = _find_last_subject_nodes(context)
    assert len(node_ids) >= 1, "沒有節點可設定 mastery"

    node_id = uuid.UUID(node_ids[0])
    nm = _create_mastery(db, user_id, node_id, float(mastery_val), 10)

    if source.upper() == "AI_INFERRED":
        nm.status = "AI_INFERRED"
    db.commit()


@given('完成度用戶 "{email}" 前 {n:d} 個節點 mastery "{mastery_val}" SM2間隔 "{interval}" 天')
def step_mastery_first_n(context, email, n, mastery_val, interval):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    node_ids = _find_last_subject_nodes(context)
    assert len(node_ids) >= n, f"節點數量不足 {n}"

    for i in range(n):
        node_id = uuid.UUID(node_ids[i])
        _create_mastery(db, user_id, node_id, float(mastery_val), int(interval))
    db.commit()


@given('完成度用戶 "{email}" 科目 "{subject_name}" 所有節點 mastery "{mastery_val}" SM2間隔 "{interval}" 天')
def step_mastery_all_in_subject(context, email, subject_name, mastery_val, interval):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    node_ids = context.ids.get(f"completion_nodes_{subject_name}", [])
    for nid_str in node_ids:
        node_id = uuid.UUID(nid_str)
        _create_mastery(db, user_id, node_id, float(mastery_val), int(interval))
    db.commit()


def _find_last_subject_nodes(context) -> list[str]:
    """取得 context.ids 中最近建立的 completion_nodes_* 節點 list。"""
    # 找到所有 completion_nodes_* 的 key
    keys = [k for k in context.ids if k.startswith("completion_nodes_")]
    if not keys:
        return []
    # 取最後一個（按 key 字典序）
    latest_key = sorted(keys)[-1]
    return context.ids[latest_key]


def _create_mastery(
    db, user_id: uuid.UUID, node_id: uuid.UUID,
    base_mastery: float, interval_days: int
) -> NodeMastery:
    """建立或更新 NodeMastery（base_mastery 作為正確率代理）。"""
    existing = (
        db.query(NodeMastery)
        .filter_by(user_id=user_id, node_id=node_id)
        .first()
    )
    now = datetime.now(timezone.utc)
    if existing:
        existing.base_mastery = base_mastery
        existing.total_count = 5
        existing.correct_count = round(base_mastery * 5)
        existing.mastery_rate = base_mastery
        existing.status = "MASTERED" if base_mastery >= 0.85 else "PENDING"
        existing.last_tested_at = now - timedelta(days=interval_days)
        existing.next_review_at = now
        return existing

    nm = NodeMastery(
        user_id=user_id,
        node_id=node_id,
        base_mastery=base_mastery,
        total_count=5,
        correct_count=round(base_mastery * 5),
        mastery_rate=base_mastery,
        status="MASTERED" if base_mastery >= 0.85 else "PENDING",
        last_tested_at=now - timedelta(days=interval_days),
        next_review_at=now,
    )
    db.add(nm)
    db.flush()
    return nm


# ─── LearningJourney 建立（考試日）──────────────────────────────────────

@given('完成度用戶 "{email}" 設定科目 "{subject_name}" 考試日距今 "{days}" 天')
def step_exam_date(context, email, subject_name, days):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    subj = _get_subject_by_name(db, context, subject_name)
    assert subj is not None, f"找不到科目 {subject_name}"

    exam_date = date.today() + timedelta(days=int(days))

    existing = (
        db.query(LearningJourney)
        .filter_by(user_id=user_id, subject_id=subj.id)
        .first()
    )
    if existing:
        existing.exam_date = exam_date
    else:
        journey = LearningJourney(
            user_id=user_id,
            subject_id=subj.id,
            exam_date=exam_date,
        )
        db.add(journey)
    db.commit()
