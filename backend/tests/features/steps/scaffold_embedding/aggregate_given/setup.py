"""Given setup — Feature 44 Scaffold embedding + 限流豁免 BDD."""

import logging
import uuid
from unittest.mock import patch

from behave import given

from app.models.resource_scaffold import ResourceScaffold


def _ensure_alice_and_resource(context, name="F44-res"):
    from tests.features.steps.sm2.aggregate_given.setup import (
        _ensure_user, _ensure_resource,
    )
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    res = _ensure_resource(db, user_id, name=name)
    db.commit()
    context.memo["last_user_id"] = user_id
    context.memo["last_resource"] = res
    return user_id, res


@given('用戶 alice 上傳 PDF 並完成 parse')
def step_alice_upload_parse_complete(context):
    """Mock _persist_parsed 寫入 scaffold + 模擬 _embed_scaffolds 寫 embedding。"""
    from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob

    user_id, res = _ensure_alice_and_resource(context, name="alice-pdf.pdf")
    db = context.db_session

    # 建 parse job + scaffold rows + 假 embedding（1024 維）
    job = ResourceParseJob(
        resource_id=res.id,
        tenant_id=res.tenant_id,
        status=ParseJobStatus.SUCCESS.value,
        gemini_model="gemini-2.5-pro",
    )
    db.add(job)

    fake_vec = [0.01] * 1024
    for i in range(3):
        sf = ResourceScaffold(
            resource_id=res.id,
            tenant_id=res.tenant_id,
            type="takeaway",
            content=f"alice-pdf scaffold {i}",
            chapter_heading=f"ch-{i}",
            template_code="K-06-study",
            embedding=fake_vec,
        )
        db.add(sf)
    db.commit()
    context.memo["parsed_resource_id"] = res.id


@given('voyage API 暫時不可用')
def step_voyage_temporarily_down(context):
    """Mock EmbeddingService.embed_texts 拋例外（_embed_scaffolds 內 best-effort catch）。"""
    patcher = patch(
        "app.services.embedding_service.EmbeddingService.embed_texts",
        side_effect=RuntimeError("voyage temporarily down (mocked)"),
    )
    patcher.start()
    if not hasattr(context, "_cleanups"):
        context._cleanups = []
    context._cleanups.append(patcher.stop)


@given('用戶 alice 有 {n} scaffolds 皆含 embedding')
def step_alice_scaffolds_with_embedding(context, n):
    user_id, res = _ensure_alice_and_resource(context, name="alice-embed-res")
    try:
        count = int(str(n).rstrip("+ "))
    except Exception:
        count = 50
    db = context.db_session
    fake_vec = [0.05] * 1024
    for i in range(count):
        sf = ResourceScaffold(
            resource_id=res.id,
            tenant_id=res.tenant_id,
            type="takeaway" if i % 2 else "pitfall",
            content=f"機器學習 條目 {i}",
            chapter_heading=f"ch-{i}",
            template_code="K-06-study",
            embedding=fake_vec,
        )
        db.add(sf)
    db.commit()
    context.memo["scaffold_count_with_embedding"] = count

    # 裝 voyage embed spy（記錄被 call 次數，預期 ≤ 1 次 — query embed）
    call_count = {"n": 0}
    real_embed = None
    try:
        from app.services.embedding_service import EmbeddingService
        real_embed = EmbeddingService.embed_texts
    except Exception:
        pass

    def _spy(self, texts, input_type=None):
        call_count["n"] += 1
        return [[0.05] * 1024 for _ in texts]

    patcher = patch(
        "app.services.embedding_service.EmbeddingService.embed_texts",
        new=_spy,
    )
    patcher.start()
    if not hasattr(context, "_cleanups"):
        context._cleanups = []
    context._cleanups.append(patcher.stop)
    context.memo["voyage_call_counter"] = call_count


@given('用戶 alice 為 FREE 方案（QPS={qps:d}）')
def step_alice_is_free(context, qps):
    """設定 alice 為 FREE plan（rate-limit middleware 以 plan 判 QPS）。"""
    from app.models.user import SubscriptionPlan, User
    user_id, _ = _ensure_alice_and_resource(context, name="F44-ratelimit-res")
    db = context.db_session
    user = db.get(User, user_id)
    user.subscription_plan = SubscriptionPlan.FREE
    db.commit()
    context.memo["expected_qps"] = qps


# 對應 F44 Scenario 3 的「reading 頁瞬間並發 12 筆 interactions ×12」前置
# Given 只需確保 alice + 1 個 scaffold 存在
@given('用戶 alice 為 FREE 方案，並有 1 個 scaffold')
def step_alice_free_with_scaffold(context):
    step_alice_is_free(context, 30)
    db = context.db_session
    res = context.memo["last_resource"]
    sf = ResourceScaffold(
        resource_id=res.id,
        tenant_id=res.tenant_id,
        type="takeaway",
        content="ratelimit-test",
        chapter_heading="ch",
        template_code="K-06-study",
    )
    db.add(sf)
    db.commit()
    context.memo["scaffold_for_interactions"] = sf.id
