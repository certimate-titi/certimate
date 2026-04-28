"""出題情境前置 — Bloom 統計 / 無考古題 / 已有 Bloom 統計。"""

import json
import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.subject import Subject, SubjectCategory


def _ensure_subject(db, name: str) -> Subject:
    subj = db.query(Subject).filter_by(name=name).first()
    if subj:
        return subj
    cat = db.query(SubjectCategory).filter_by(name="Bloom 測試分類").first()
    if not cat:
        cat = SubjectCategory(name="Bloom 測試分類")
        db.add(cat)
        db.flush()
    subj = Subject(name=name, category_id=cat.id)
    db.add(subj)
    db.flush()
    return subj


def _ensure_node_for_subject(context, subj: Subject) -> KnowledgeNode:
    db = context.db_session
    existing = db.query(KnowledgeNode).filter_by(subject_id=subj.id).first()
    if existing:
        if not existing.available_questions:
            existing.available_questions = 100
            db.commit()
        context.ids[f"node_{subj.name}"] = str(existing.id)
        return existing
    node = KnowledgeNode(
        subject_id=subj.id,
        name=f"{subj.name} 預設節點",
        depth=1,
        available_questions=100,
    )
    db.add(node)
    db.commit()
    context.ids[f"node_{subj.name}"] = str(node.id)
    return node


@given('學科 "{subject_name}" 的歷年考古題 Bloom 統計為：')
def step_subject_bloom_stats(context, subject_name):
    db = context.db_session
    subj = _ensure_subject(db, subject_name)

    bloom_stats = {}
    for row in context.table:
        bloom_stats[row["bloom_category"]] = int(row["suggested_percentage"])

    subj.description = json.dumps({"bloom_stats": bloom_stats})
    subj.available_questions = max(subj.available_questions or 0, 100)
    db.commit()

    _ensure_node_for_subject(context, subj)
    context.memo.setdefault("bloom_stats", {})[subject_name] = bloom_stats


@given('學科 "{subject_name}" 無任何考古題資料')
def step_subject_no_historical(context, subject_name):
    db = context.db_session
    subj = _ensure_subject(db, subject_name)
    # 確保沒有 bloom_stats 在 description
    subj.description = None
    subj.available_questions = max(subj.available_questions or 0, 100)
    db.commit()
    _ensure_node_for_subject(context, subj)


@given('學科 "{subject_name}" 有考古題 Bloom 統計')
def step_subject_has_bloom_stats(context, subject_name):
    db = context.db_session
    subj = _ensure_subject(db, subject_name)

    if not subj.description or "bloom_stats" not in (subj.description or ""):
        default_stats = {
            "remember": 40, "understand": 30, "apply": 20,
            "analyze": 7, "evaluate": 2, "create": 1,
        }
        subj.description = json.dumps({"bloom_stats": default_stats})
    subj.available_questions = max(subj.available_questions or 0, 100)
    db.commit()
    _ensure_node_for_subject(context, subj)
