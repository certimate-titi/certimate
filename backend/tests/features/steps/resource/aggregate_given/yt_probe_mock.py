"""Given setup — mock yt-dlp probe bot challenge failure.

P0-2 hot-fix：模擬 yt-dlp._get_video_title 在 bot challenge 下拋出 Exception，
驗證 submit_youtube 走 oEmbed fallback 不中斷。
"""

from unittest.mock import patch, MagicMock

from behave import given


def _add_patcher(context, patcher):
    """Helper：啟動 patcher 並存入 context.memo 供 after_scenario 清理。"""
    patcher.start()
    if "_patches" not in context.memo:
        context.memo["_patches"] = []
    context.memo["_patches"].append(patcher)


@given('yt-dlp probe 模擬 bot challenge 失敗')
def step_mock_yt_dlp_bot_challenge(context):
    """Patch resource_service._fetch_youtube_title_oembed 讓 yt-dlp 路徑失敗，
    但 oEmbed 路徑由另一個 step 控制。

    這裡 patch yt_dlp.YoutubeDL 的 extract_info 拋 bot challenge exception。
    """
    patcher = patch(
        "yt_dlp.YoutubeDL",
        side_effect=Exception("Sign in to confirm you're not a bot"),
    )
    _add_patcher(context, patcher)


@given('oEmbed API 模擬回傳 title "{title}"')
def step_mock_oembed_response(context, title):
    """Patch resource_service._fetch_youtube_title_oembed 回傳固定 title。"""
    patcher = patch(
        "app.services.resource_service._fetch_youtube_title_oembed",
        return_value=title,
    )
    _add_patcher(context, patcher)
