"""Given — 使用者今日已使用 AI 對話指定次數。"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.user_usage import UserUsage


@given('使用者 "{email}" 今日已使用 AI 對話 {count:d} 次')
def step_ai_usage_today(context, email, count):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    period = datetime.now(timezone.utc).strftime("%Y-%m")

    usage = db.query(UserUsage).filter_by(user_id=user_id, period=period).first()
    if usage is None:
        usage = UserUsage(user_id=user_id, period=period)
        db.add(usage)
    usage.daily_ai_chats_used = count
    db.commit()
