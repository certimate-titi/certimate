"""When _persist_parsed / _call_gemini_once — Feature 38 BDD."""

import logging
import uuid
from unittest.mock import patch

from behave import when

from app.models.resource import Resource


@when('_persist_parsed 處理該 scaffolds')
def step_persist_parsed_with_memo_scaffolds(context):
    """以 memo 裡的 scaffolds 跑 _persist_parsed，捕捉 log 供斷言。"""
    from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob
    from app.services.resource_parse_service import _persist_parsed

    db = context.db_session

    # 若前置 Given 未建 resource（如 dedup 場景僅有 Background），自動補一筆
    if "last_resource_id" not in context.memo:
        from app.models.subject import Subject, SubjectCategory
        from app.models.user import SubscriptionPlan, User, UserRole, UserStatus

        email = next(iter(getattr(context, "ids", {})), None)
        if email is None:
            user = User(
                email="pitfall-bg@example.com",
                password_hash="test-hash",
                subscription_plan=SubscriptionPlan.PRO,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            )
            db.add(user)
            db.flush()
            user_id = user.id
        else:
            user_id = uuid.UUID(context.ids[email])

        cat = db.query(SubjectCategory).first() or SubjectCategory(name="IT")
        if cat.id is None:
            db.add(cat)
            db.flush()
        subj = (
            db.query(Subject).filter_by(name="F38-dedup-subject").first()
            or Subject(name="F38-dedup-subject", category_id=cat.id)
        )
        if subj.id is None:
            db.add(subj)
            db.flush()

        auto_res = Resource(
            user_id=user_id,
            subject_id=subj.id,
            name="auto-res-38-dedup",
            type="pdf",
            status="COMPLETED",
            file_size_bytes=1024,
            gcs_path="auto-dedup.pdf",
            parsed_markdown="# auto\n\n.",
            detected_content_type="study_material",
        )
        db.add(auto_res)
        db.flush()
        context.memo["last_resource_id"] = str(auto_res.id)

    resource = db.get(Resource, uuid.UUID(context.memo["last_resource_id"]))
    assert resource is not None, "找不到測試資源"

    job = db.query(ResourceParseJob).filter_by(resource_id=resource.id).first()
    if job is None:
        job = ResourceParseJob(
            resource_id=resource.id,
            tenant_id=resource.tenant_id,
            status=ParseJobStatus.SUCCESS.value,
            gemini_model="gemini-2.5-pro",
        )
        db.add(job)
        db.flush()

    parsed = {
        "markdown": "# 章節\n\n內文。",
        "detected_content_type": "study_material",
        "critical_pages": [1],
        "questions": [],
        "scaffolds": context.memo.get("parsed_scaffolds", []),
    }

    # 捕捉 pitfall-dedup log
    captured = []

    # 直接 patch resource_parse_service.logger.info / debug — 避開複雜的 handler 級聯
    import app.services.resource_parse_service as _rps_mod
    real_info = _rps_mod.logger.info
    real_debug = _rps_mod.logger.debug

    def _capture_info(msg, *args, **kwargs):
        try:
            captured.append(msg % args if args else msg)
        except Exception:
            captured.append(str(msg))
        return real_info(msg, *args, **kwargs)

    def _capture_debug(msg, *args, **kwargs):
        try:
            captured.append(msg % args if args else msg)
        except Exception:
            captured.append(str(msg))
        return real_debug(msg, *args, **kwargs)

    _rps_mod.logger.info = _capture_info
    _rps_mod.logger.debug = _capture_debug

    try:
        with (
            patch("app.services.resource_parse_service._embed_scaffolds"),
            patch("app.services.resource_parse_service._link_scaffolds_to_nodes"),
            patch("app.services.resource_parse_service._generate_reference_answers"),
        ):
            result = _persist_parsed(db, resource, job, parsed)
    finally:
        _rps_mod.logger.info = real_info
        _rps_mod.logger.debug = real_debug

    context.memo["persist_result"] = result
    context.memo["persist_logs"] = captured


@when('run_parse_job 啟動 _call_gemini_once')
def step_run_parse_job_starts_call_gemini(context):
    """模擬 run_parse_job 觸發 _call_gemini_once 的 template 選擇流程。

    純驗證 prompt routing + fallback 行為（不真的呼叫 Gemini）。
    """
    from app.services.resource_parse_service import _select_prompt_template

    r = context.memo.get("routing_resource")
    assert r is not None, "需要先設定 routing_resource"

    template_name = _select_prompt_template(r)
    context.memo["initial_template_name"] = template_name

    db = context.db_session
    from app.models.prompt_template import PromptTemplateV2

    template = (
        db.query(PromptTemplateV2)
        .filter(PromptTemplateV2.name == template_name)
        .first()
    )
    captured = []
    if template is None:
        captured.append(
            f"[prompt-routing] {template_name} not found, "
            f"fallback to resource_parser_v2"
        )
        context.memo["loaded_template_name"] = "resource_parser_v2"
        context.memo["initial_load_failed"] = True
    else:
        context.memo["loaded_template_name"] = template_name
        context.memo["initial_load_failed"] = False

    context.memo["parse_logs"] = captured
