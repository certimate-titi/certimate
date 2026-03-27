"""Then 使用者的已使用次數應重置為 0 — Aggregate Then"""

import uuid
from datetime import datetime, timezone

from behave import then

from app.models.user_usage import UserUsage


@then('使用者 "{email}" 的 AI 對話已使用次數應重置為 {count:d}')
def step_impl_ai(context, email, count):
    db = context.db_session
    db.expire_all()
    user_uuid = uuid.UUID(context.ids[email])
    now = datetime.now(timezone.utc)
    period = now.strftime("%Y-%m")

    usage = db.query(UserUsage).filter_by(user_id=user_uuid, period=period).first()
    if usage:
        assert usage.daily_ai_chats_used == count, (
            f"預期 AI 對話已使用 {count}，實際 {usage.daily_ai_chats_used}"
        )
    else:
        # 沒有 usage 紀錄表示已重置或尚未使用
        assert count == 0, f"預期使用次數 {count}，但無使用紀錄"


@then('使用者 "{email}" 的上傳已使用次數應重置為 {count:d}')
def step_impl_upload(context, email, count):
    db = context.db_session
    db.expire_all()
    user_uuid = uuid.UUID(context.ids[email])
    now = datetime.now(timezone.utc)
    period = now.strftime("%Y-%m")

    usage = db.query(UserUsage).filter_by(user_id=user_uuid, period=period).first()
    if usage:
        assert usage.monthly_uploads_used == count, (
            f"預期上傳已使用 {count}，實際 {usage.monthly_uploads_used}"
        )
    else:
        assert count == 0, f"預期使用次數 {count}，但無使用紀錄"
