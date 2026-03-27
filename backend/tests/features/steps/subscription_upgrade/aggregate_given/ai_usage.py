"""Given 使用者當月已使用 AI 對話 N 次 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.user_usage import UserUsage


@given('使用者 "{email}" 當月已使用 AI 對話 {count:d} 次')
def step_impl(context, email, count):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    now = datetime.now(timezone.utc)
    period = now.strftime("%Y-%m")

    usage = db.query(UserUsage).filter_by(user_id=user_uuid, period=period).first()
    if not usage:
        usage = UserUsage(
            user_id=user_uuid,
            period=period,
            daily_ai_chats_used=count,
            monthly_uploads_used=0,
            monthly_exams_used=0,
            monthly_vision_pages_used=0,
        )
        db.add(usage)
    else:
        usage.daily_ai_chats_used = count

    db.commit()
