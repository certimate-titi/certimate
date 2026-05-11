"""When step actions — Feature 44 BDD."""

import logging
import time
import uuid
from unittest.mock import patch

from behave import when

from app.models.resource_scaffold import ResourceScaffold


@when('查詢產出的 resource_scaffolds')
def step_query_persisted_scaffolds(context):
    """讀回 alice 該 resource 的 scaffold 清單存 memo。"""
    db = context.db_session
    res_id = context.memo["parsed_resource_id"]
    rows = (
        db.query(ResourceScaffold)
        .filter_by(resource_id=res_id)
        .all()
    )
    context.memo["queried_scaffolds"] = rows


@when('parse pipeline 跑 _embed_scaffolds')
def step_run_embed_scaffolds(context):
    """直接呼叫 _embed_scaffolds 觀察行為（voyage 已 mock 為失敗）。"""
    from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob
    from app.services.resource_parse_service import _embed_scaffolds
    from tests.features.steps.scaffold_embedding.aggregate_given.setup import (
        _ensure_alice_and_resource,
    )

    db = context.db_session
    if "last_user_id" not in context.memo:
        _ensure_alice_and_resource(context, name="F44-embed-fail-res")
    user_id = context.memo["last_user_id"]
    res = context.memo["last_resource"]
    job = (
        db.query(ResourceParseJob)
        .filter_by(resource_id=res.id)
        .first()
    )
    if job is None:
        job = ResourceParseJob(
            resource_id=res.id,
            tenant_id=res.tenant_id,
            status=ParseJobStatus.SUCCESS.value,
            gemini_model="gemini-2.5-pro",
        )
        db.add(job)
        db.flush()

    # 確保至少有一筆 scaffold 待 embed
    if not db.query(ResourceScaffold).filter_by(resource_id=res.id).first():
        sf = ResourceScaffold(
            resource_id=res.id,
            tenant_id=res.tenant_id,
            type="takeaway",
            content="待 embed",
            chapter_heading="ch",
            template_code="K-06-study",
        )
        db.add(sf)
        db.commit()

    rows = db.query(ResourceScaffold).filter_by(resource_id=res.id).all()

    # 捕捉 logger
    captured = []

    class _H(logging.Handler):
        def emit(self, record):
            try:
                captured.append(record.getMessage())
            except Exception:
                captured.append(str(record.msg))

    import app.services.resource_parse_service as _rps_mod
    real_info = _rps_mod.logger.info
    real_warn = _rps_mod.logger.warning

    def _capture(level_orig):
        def _f(msg, *args, **kwargs):
            try:
                captured.append(msg % args if args else msg)
            except Exception:
                captured.append(str(msg))
            return level_orig(msg, *args, **kwargs)
        return _f

    _rps_mod.logger.info = _capture(real_info)
    _rps_mod.logger.warning = _capture(real_warn)
    try:
        try:
            _embed_scaffolds(rows)
            db.commit()
        except Exception:
            db.rollback()
    finally:
        _rps_mod.logger.info = real_info
        _rps_mod.logger.warning = real_warn

    context.memo["parse_logs"] = captured
    context.memo["queried_scaffolds"] = (
        db.query(ResourceScaffold).filter_by(resource_id=res.id).all()
    )


@when('1 秒內並發 POST /api/v1/resource-scaffolds/{{id}}/interactions × {n:d}')
def step_concurrent_interactions(context, n):
    """串行發 N 筆 interactions log 到該 scaffold（測 path-exempt rate limit）。"""
    from tests.features.steps.sm2.commands.actions import (
        _resolve_user_id, _auth_headers,
    )
    from tests.features.steps.scaffold_embedding.aggregate_given.setup import (
        step_alice_free_with_scaffold,
    )
    if "scaffold_for_interactions" not in context.memo:
        step_alice_free_with_scaffold(context)
    user_id = _resolve_user_id(context)
    sf_id = context.memo["scaffold_for_interactions"]
    headers = _auth_headers(context, user_id)
    # 用 recall_self_rated（next_review_at 有值，避開 dict[str,str] response 驗證 bug）
    body = {"event": "recall_self_rated", "recall_quality": "full"}
    responses = []
    start = time.time()
    for _ in range(n):
        r = context.api_client.post(
            f"/api/v1/resource-scaffolds/{sf_id}/interactions",
            json=body,
            headers=headers,
        )
        responses.append(r)
    elapsed = time.time() - start
    context.memo["interactions_responses"] = responses
    context.memo["interactions_elapsed"] = elapsed


@when('1 秒內並發 GET /api/v1/resources × {n:d}')
def step_concurrent_resources_get(context, n):
    from tests.features.steps.sm2.commands.actions import (
        _resolve_user_id, _auth_headers,
    )
    user_id = _resolve_user_id(context)
    headers = _auth_headers(context, user_id)
    responses = []
    for _ in range(n):
        r = context.api_client.get("/api/v1/resources", headers=headers)
        responses.append(r)
    context.memo["resources_responses"] = responses


# GET /concept-center?q={q} 共用 F43 的 step（semantic_search/commands/actions.py）
# F44 需偵測「不再 call voyage embed」— 由 _install_embed_spy 在 Given 階段裝 spy
# 並由 _check_voyage_calls Then 步驟讀取結果（context.memo["concept_voyage_calls"]）。
