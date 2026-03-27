"""Given 系統中有以下 AI 冷卻紀錄 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.ai_cooldown import AiCooldown


@given('系統中有以下 AI 冷卻紀錄：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        user_id_key = row["使用者 ID"].strip()
        reason = row["原因"]
        cooldown_until_str = row["冷卻結束時間"]

        user_uuid = uuid.UUID(context.ids[user_id_key])
        cooldown_until = datetime.fromisoformat(cooldown_until_str).replace(tzinfo=timezone.utc)

        cooldown = AiCooldown(
            user_id=user_uuid,
            reason=reason,
            cooldown_until=cooldown_until,
        )
        db.add(cooldown)

    db.commit()
