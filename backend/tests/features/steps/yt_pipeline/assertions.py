"""F47 BDD assertions — YouTube Gemini direct pipeline.

When steps 均 mock：
  1. _check_youtube_duration  → 控制時長
  2. enqueue_process_resource → 避免真實 Cloud Tasks 呼叫

Then steps：
  - F47 專用業務斷言（擷取器無 yt-dlp / 配額消耗 / 退回）
  - 通用「錯誤訊息應包含 "{text}"」（補充既有 common_then 中文括號版）
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

from behave import then, given, when

from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob


# ─────────────────────────────────────────────────────────────────────────────
# When
# ─────────────────────────────────────────────────────────────────────────────

@when('使用者 "{email}" 提交超過 30 分鐘的 YouTube URL，科目為 {subject_id:d}')
def step_submit_long_youtube(context, email, subject_id):
    """提交一個標記為超長的 YouTube URL（mock duration check 回傳 45 分鐘）。"""
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    with patch("app.api.resource._check_youtube_duration", return_value=45.0):
        response = context.api_client.post(
            "/api/v1/resources/youtube",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "youtube_url": "https://www.youtube.com/watch?v=long123",
                "subject_id": subject_uuid,
            },
        )
    context.last_response = response



@when('使用者 "{email}" 提交 YouTube URL 但背景排程失敗，科目為 {subject_id:d}')
def step_submit_youtube_enqueue_fail(context, email, subject_id):
    """提交 YouTube URL，但 enqueue 失敗（mock EnqueueFailedError）。"""
    from app.services.cloud_tasks_service import EnqueueFailedError

    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    with patch("app.api.resource._check_youtube_duration", return_value=10.0), \
         patch(
             "app.services.cloud_tasks_service.enqueue_process_resource",
             side_effect=EnqueueFailedError("Cloud Tasks 測試失敗"),
         ):
        response = context.api_client.post(
            "/api/v1/resources/youtube",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "youtube_url": "https://www.youtube.com/watch?v=abc123",
                "subject_id": subject_uuid,
            },
        )
    context.last_response = response


# ─────────────────────────────────────────────────────────────────────────────
# Then
# ─────────────────────────────────────────────────────────────────────────────

@then("YouTube 擷取器不匯入 yt_dlp 模組")
def step_no_yt_dlp_import(context):
    """驗證 youtube_extractor 模組原始碼不含 yt_dlp import。"""
    import inspect
    from app.services.media_extractors import youtube_extractor
    source = inspect.getsource(youtube_extractor)
    assert "import yt_dlp" not in source, "youtube_extractor 仍有 yt_dlp import"
    assert "from yt_dlp" not in source, "youtube_extractor 仍有 from yt_dlp import"


@then("YouTube 擷取器不匯入 openai whisper 模組")
def step_no_openai_whisper_import(context):
    """驗證 youtube_extractor 模組不含 openai Whisper import 語句。"""
    import inspect
    import re
    from app.services.media_extractors import youtube_extractor
    source = inspect.getsource(youtube_extractor)
    # 只檢查 import 語句（非 docstring 提及）
    import_lines = [
        line for line in source.split("\n")
        if re.match(r"\s*(import|from)\s+", line)
    ]
    import_block = "\n".join(import_lines)
    assert "whisper" not in import_block.lower(), (
        f"youtube_extractor 仍有 whisper import:\n{import_block}"
    )


@then('使用者 "{email}" 本月 YouTube 配額已消耗 2 份')
def step_assert_quota_consumed_2(context, email):
    """確認本月 parse jobs 計數增加了 2（YouTube = 2 份配額）。"""
    from app.services.resource_parse_quota_service import get_usage_this_month
    db = context.db_session
    db.expire_all()
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"

    used = get_usage_this_month(db, uuid.UUID(user_id))
    assert used == 2, f"預期配額消耗 2 份，實際為 {used} 份"


@then('使用者 "{email}" 本月 YouTube 配額已退回 2 份')
def step_assert_quota_refunded(context, email):
    """確認 EnqueueFailedError 後配額已退回（usage = 0）。"""
    from app.services.resource_parse_quota_service import get_usage_this_month
    db = context.db_session
    # 重新載入 session 確保看到最新狀態
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
