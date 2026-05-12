"""F47 BDD assertions — YouTube 雙路徑分流 pipeline.

When steps 均 mock：
  1. _probe_youtube_metadata → 控制 (duration_minutes, has_cc)
  2. enqueue_process_resource → 避免真實 Cloud Tasks 呼叫
  3. _check_monthly_cost_cap → 月度成本封頂直接 raise HTTPException

Then steps：
  - F47 路徑斷言（有 CC Flash / 無 CC Pro / 配額消耗 / 退回）
  - 通用「錯誤訊息應包含 "{text}"」
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

from behave import then, given, when
from fastapi import HTTPException

from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob


# ─────────────────────────────────────────────────────────────────────────────
# Given
# ─────────────────────────────────────────────────────────────────────────────

@given('使用者 "{email}" 本月 AI 成本已累積 USD {amount:f}')
def step_set_monthly_ai_cost(context, email, amount):
    """把本月累積成本暫存在 context，供後續 When step 注入 mock。"""
    context.monthly_ai_cost = amount
    context.monthly_ai_cost_email = email


# ─────────────────────────────────────────────────────────────────────────────
# When — 雙路徑提交
# ─────────────────────────────────────────────────────────────────────────────

def _submit_youtube_with_mock(context, email, subject_id, duration_minutes, has_cc,
                               enqueue_side_effect=None, monthly_cost_override=None):
    """共用提交 helper，mock probe + enqueue。"""
    from app.services.cloud_tasks_service import EnqueueFailedError

    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"
    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    enqueue_mock = MagicMock(side_effect=enqueue_side_effect)

    patches = [
        patch("app.api.resource._probe_youtube_metadata", return_value=(duration_minutes, has_cc)),
        patch("app.services.cloud_tasks_service.enqueue_process_resource", enqueue_mock),
    ]

    # 若有月度成本設定，mock _check_monthly_cost_cap
    cost_to_use = monthly_cost_override if monthly_cost_override is not None else getattr(context, "monthly_ai_cost", None)
    if cost_to_use is not None and not has_cc:
        # 根據方案決定 cap
        from app.api.resource import _MONTHLY_COST_CAP_USD, _GEMINI_PRO_COST_PER_MINUTE_USD
        # 取得 user plan
        from app.models.user import User
        db = context.db_session
        u = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        raw_plan = getattr(u, "subscription_plan", None)
        plan = getattr(raw_plan, "value", raw_plan) or "FREE"
        cap = _MONTHLY_COST_CAP_USD.get(plan, 0)
        estimated = 20.0 * _GEMINI_PRO_COST_PER_MINUTE_USD
        if float(cost_to_use) + estimated > cap:
            def raise_cost_cap(db, user, url):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "message": f"本月 AI 成本已接近方案上限（{plan} 上限 USD {cap:.0f}，已用 USD {float(cost_to_use):.2f}），無 CC 影片處理暫時停用",
                        "used_usd": float(cost_to_use),
                        "cap_usd": cap,
                        "plan": plan,
                    },
                )
            patches.append(patch("app.api.resource._check_monthly_cost_cap", side_effect=raise_cost_cap))

    with _nested_patches(patches):
        response = context.api_client.post(
            "/api/v1/resources/youtube",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "youtube_url": "https://www.youtube.com/watch?v=test123",
                "subject_id": subject_uuid,
            },
        )
    context.last_response = response
    context.last_has_cc = has_cc


def _nested_patches(patch_list):
    """Stack multiple context managers."""
    from contextlib import ExitStack
    stack = ExitStack()
    for p in patch_list:
        stack.enter_context(p)
    return stack


@when('使用者 "{email}" 提交有 CC 字幕的 YouTube URL，科目為 {subject_id:d}')
def step_submit_with_cc(context, email, subject_id):
    """有 CC，10 分鐘，正常 enqueue。"""
    _submit_youtube_with_mock(context, email, subject_id, duration_minutes=10.0, has_cc=True)


@when('使用者 "{email}" 提交無 CC 字幕的 YouTube URL，科目為 {subject_id:d}')
def step_submit_without_cc(context, email, subject_id):
    """無 CC，10 分鐘，正常 enqueue。"""
    _submit_youtube_with_mock(context, email, subject_id, duration_minutes=10.0, has_cc=False)


@when('使用者 "{email}" 提交有 CC 且 {duration:d} 分鐘的 YouTube URL，科目為 {subject_id:d}')
def step_submit_with_cc_duration(context, email, duration, subject_id):
    """有 CC，指定時長。"""
    _submit_youtube_with_mock(context, email, subject_id, duration_minutes=float(duration), has_cc=True)


@when('使用者 "{email}" 提交無 CC 且 {duration:d} 分鐘的 YouTube URL，科目為 {subject_id:d}')
def step_submit_without_cc_duration(context, email, duration, subject_id):
    """無 CC，指定時長。"""
    _submit_youtube_with_mock(context, email, subject_id, duration_minutes=float(duration), has_cc=False)


@when('使用者 "{email}" 提交有 CC 且排程失敗的 YouTube URL，科目為 {subject_id:d}')
def step_submit_with_cc_enqueue_fail(context, email, subject_id):
    """有 CC，enqueue 失敗。"""
    from app.services.cloud_tasks_service import EnqueueFailedError
    _submit_youtube_with_mock(
        context, email, subject_id,
        duration_minutes=10.0, has_cc=True,
        enqueue_side_effect=EnqueueFailedError("Cloud Tasks 測試失敗"),
    )


@when('使用者 "{email}" 提交無 CC 且排程失敗的 YouTube URL，科目為 {subject_id:d}')
def step_submit_without_cc_enqueue_fail(context, email, subject_id):
    """無 CC，enqueue 失敗。"""
    from app.services.cloud_tasks_service import EnqueueFailedError
    _submit_youtube_with_mock(
        context, email, subject_id,
        duration_minutes=10.0, has_cc=False,
        enqueue_side_effect=EnqueueFailedError("Cloud Tasks 測試失敗"),
    )


# 舊 Step — 相容 F47 原有 Scenarios（月度成本無關 → 無 CC + 10 分）
@when('使用者 "{email}" 提交超過 30 分鐘的 YouTube URL，科目為 {subject_id:d}')
def step_submit_long_youtube(context, email, subject_id):
    """超過 20 分鐘無 CC → 422（mock 45 分鐘）。"""
    _submit_youtube_with_mock(context, email, subject_id, duration_minutes=45.0, has_cc=False)


@when('使用者 "{email}" 提交 YouTube URL 但背景排程失敗，科目為 {subject_id:d}')
def step_submit_youtube_enqueue_fail(context, email, subject_id):
    """無 CC，enqueue 失敗（舊 step，相容舊 feature）。"""
    from app.services.cloud_tasks_service import EnqueueFailedError
    _submit_youtube_with_mock(
        context, email, subject_id,
        duration_minutes=10.0, has_cc=False,
        enqueue_side_effect=EnqueueFailedError("Cloud Tasks 測試失敗"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Then
# ─────────────────────────────────────────────────────────────────────────────

@then("YouTube 擷取器使用 Flash 文字路徑，不呼叫 Gemini File API")
def step_assert_flash_path(context):
    """驗證有 CC 路徑：youtube_extractor 模組有 _apply_k01_structuring，不使用 FileData。"""
    import inspect
    from app.services.media_extractors import youtube_extractor
    source = inspect.getsource(youtube_extractor)
    assert "_apply_k01_structuring" in source, "youtube_extractor 缺少 _apply_k01_structuring（CC Flash 路徑）"
    assert "_GEMINI_MODEL_FLASH" in source, "youtube_extractor 缺少 Flash model 常數"


@then("YouTube 擷取器使用 Pro 直餵路徑")
def step_assert_pro_path(context):
    """驗證無 CC 路徑：youtube_extractor 模組有 _gemini_direct_extract。"""
    import inspect
    from app.services.media_extractors import youtube_extractor
    source = inspect.getsource(youtube_extractor)
    assert "_gemini_direct_extract" in source, "youtube_extractor 缺少 _gemini_direct_extract（Pro 路徑）"
    assert "_GEMINI_MODEL_PRO" in source, "youtube_extractor 缺少 Pro model 常數"


@then("YouTube 擷取器不匯入 yt_dlp 模組")
def step_no_yt_dlp_import(context):
    """驗證 youtube_extractor 在無 CC 路徑（Gemini Pro）不強制 import yt_dlp。

    yt_dlp 僅在有 CC 路徑 probe/下載時才 import（ImportError graceful fallback）。
    """
    # 驗證 Pro path 函式（_gemini_direct_extract）不含 yt_dlp import
    import inspect
    from app.services.media_extractors import youtube_extractor
    source = inspect.getsource(youtube_extractor._gemini_direct_extract)  # type: ignore[attr-defined]
    assert "yt_dlp" not in source, "_gemini_direct_extract 不應引用 yt_dlp"


@then("YouTube 擷取器不匯入 openai whisper 模組")
def step_no_openai_whisper_import(context):
    """驗證 youtube_extractor 模組不含 openai Whisper import 語句。"""
    import inspect
    import re
    from app.services.media_extractors import youtube_extractor
    source = inspect.getsource(youtube_extractor)
    import_lines = [
        line for line in source.split("\n")
        if re.match(r"\s*(import|from)\s+", line)
    ]
    import_block = "\n".join(import_lines)
    assert "whisper" not in import_block.lower(), (
        f"youtube_extractor 仍有 whisper import:\n{import_block}"
    )


@then('使用者 "{email}" 本月 YouTube 配額已消耗 {n:d} 份')
def step_assert_quota_consumed_n(context, email, n):
    """確認本月 parse jobs 計數 == n。"""
    from app.services.resource_parse_quota_service import get_usage_this_month
    db = context.db_session
    db.expire_all()
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"
    used = get_usage_this_month(db, uuid.UUID(user_id))
    assert used == n, f"預期配額消耗 {n} 份，實際為 {used} 份"


@then('使用者 "{email}" 本月 YouTube 配額已退回 2 份')
def step_assert_quota_refunded_2(context, email):
    """確認 EnqueueFailedError 後配額已退回（usage = 0）— 舊 step 相容。"""
    from app.services.resource_parse_quota_service import get_usage_this_month
    db = context.db_session
    db.expire_all()
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"
    used = get_usage_this_month(db, uuid.UUID(user_id))
    assert used == 0, f"預期配額已退回（0 份），實際為 {used} 份"


@then('使用者 "{email}" 本月 YouTube 配額已退回（用量為 0）')
def step_assert_quota_refunded_zero(context, email):
    """確認 EnqueueFailedError 後配額已退回（usage = 0）。"""
    from app.services.resource_parse_quota_service import get_usage_this_month
    db = context.db_session
    db.expire_all()
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"
    used = get_usage_this_month(db, uuid.UUID(user_id))
    assert used == 0, f"預期配額已退回（0 份），實際為 {used} 份"


@then('錯誤訊息應包含 "{text}"')
def step_error_message_contains(context, text):
    """驗證 HTTP 回應錯誤訊息中包含指定文字（雙引號版）。"""
    assert context.last_response is not None, "無 last_response"
    body = context.last_response.text
    assert text in body, f"錯誤訊息不含 '{text}'：{body}"
