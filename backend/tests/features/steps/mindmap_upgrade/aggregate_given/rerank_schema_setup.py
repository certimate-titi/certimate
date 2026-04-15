"""Given — Rerank / Schema / env-var specific setup for Q1-Q4 補強."""

import os
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceStatus, ResourceType
from app.models.resource_chunk import ResourceChunk
from app.models.subject import Subject, SubjectCategory


def _ensure_subject(db, name: str = "BDD Rerank Subject"):
    cat = db.query(SubjectCategory).first()
    if cat is None:
        cat = SubjectCategory(name="BDD Cat")
        db.add(cat)
        db.flush()
    subj = db.query(Subject).filter(Subject.name == name).first()
    if subj is None:
        subj = Subject(name=name, category_id=cat.id)
        db.add(subj)
        db.flush()
    return subj.id


def _ensure_user(db, context):
    for key, uid in context.ids.items():
        if "@" in key:
            return uuid.UUID(uid)
    raise AssertionError("no user in context.ids")


def _make_resource(db, user_id, subject_id, name):
    r = Resource(
        user_id=user_id, subject_id=subject_id, name=name,
        type=ResourceType.PDF, status=ResourceStatus.COMPLETED,
    )
    db.add(r); db.flush()
    return r.id


@given('RetrievalService 已啟用 rerank')
def step_rerank_enabled(context):
    os.environ["RETRIEVAL_RERANK_ENABLED"] = "true"
    context.memo["_rerank_enabled_set"] = True


@given('候選池只有 {n:d} 個 chunks')
def step_small_candidate_pool(context, n):
    db = context.db_session
    user_id = _ensure_user(db, context)
    sid = _ensure_subject(db, "BDD Rerank Small")
    rid = _make_resource(db, user_id, sid, "rerank-small.pdf")
    context.memo["rerank_resource_id"] = str(rid)

    for i in range(n):
        chunk = ResourceChunk(
            resource_id=rid, node_id=None, chunk_index=i,
            content=f"chunk {i}", token_count=10,
            embedding=[0.1] * 1024,
        )
        db.add(chunk)
    db.commit()
    context.memo["rerank_candidate_count"] = n


@given('候選池有 {n:d} 個 chunks')
def step_candidate_pool(context, n):
    step_small_candidate_pool(context, n)


@given('Voyage AI 當月用量達 degrade 門檻')
def step_voyage_degraded(context):
    from decimal import Decimal
    from app.models.budget_config import BudgetConfig
    from app.models.ai_usage_ledger import AiUsageLedger

    db = context.db_session
    config = db.query(BudgetConfig).filter(BudgetConfig.scope == "AI_VOYAGE").first()
    if config is None:
        config = BudgetConfig(
            scope="AI_VOYAGE",
            monthly_limit_usd=Decimal("50"),
            warning_percent=50,
            degrade_percent=80,
            disable_percent=100,
            gcp_sync_enabled=False,
        )
        db.add(config)
    # write ledger row = 80% of limit
    db.query(AiUsageLedger).filter(AiUsageLedger.provider == "voyage").delete()
    db.add(
        AiUsageLedger(
            provider="voyage", endpoint="bdd/synthetic",
            input_tokens=0, output_tokens=0,
            cost_usd=Decimal("40"),  # = 80% of 50
            feature="bdd_given",
        )
    )
    db.commit()


@given('Voyage rerank API 會拋出例外')
def step_rerank_api_error(context):
    """Patch EmbeddingService.rerank to raise for the next call."""
    context.memo["_rerank_will_fail"] = True


@given('環境變數 GEMINI_UNIFIED_EXTRACTION_MODEL 未設定')
def step_gemini_env_unset(context):
    if "GEMINI_UNIFIED_EXTRACTION_MODEL" in os.environ:
        context.memo["_saved_gemini_model_env"] = os.environ.pop(
            "GEMINI_UNIFIED_EXTRACTION_MODEL"
        )


@given('環境變數 GEMINI_UNIFIED_EXTRACTION_MODEL 設為 "{model}"')
def step_gemini_env_set(context, model):
    context.memo["_saved_gemini_model_env"] = os.environ.get(
        "GEMINI_UNIFIED_EXTRACTION_MODEL"
    )
    os.environ["GEMINI_UNIFIED_EXTRACTION_MODEL"] = model


@given('Gemini 回傳 schema 格式錯誤')
def step_gemini_schema_rejected(context):
    context.memo["_gemini_schema_will_fail"] = True
