"""Given 使用者本月已上傳 N 次 — Aggregate Given"""

import uuid
from datetime import datetime

from behave import given

from app.models.user_usage import UserUsage


@given('使用者 "{email}" 本月已上傳 {count:d} 次')
def step_impl(context, email, count):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    db = context.db_session
    uid = uuid.UUID(context.ids[email])
    period = datetime.now().strftime("%Y-%m")

    usage = db.query(UserUsage).filter_by(user_id=uid, period=period).first()
    if not usage:
        usage = UserUsage(user_id=uid, period=period, monthly_uploads_used=count)
        db.add(usage)
    else:
        usage.monthly_uploads_used = count
    db.commit()
