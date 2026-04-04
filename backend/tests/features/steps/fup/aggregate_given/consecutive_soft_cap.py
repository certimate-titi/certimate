"""Given — 使用者連續多天觸發 soft cap 告警。"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.audit_log import AdminAuditLog


@given('使用者 "{email}" 連續 {days:d} 天觸發 soft cap 告警')
def step_consecutive_soft_cap(context, email, days):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    now = datetime.now(timezone.utc)
    for i in range(days):
        log = AdminAuditLog(
            admin_id=user_id,
            action="fup_soft_cap_triggered",
            target_type="user",
            target_id=user_id,
            details={"daily_usage": 1001, "day": i + 1},
            created_at=now - timedelta(days=days - 1 - i),
        )
        db.add(log)
    db.commit()
