"""Then AI 教練冷卻提示與後續拒絕驗證 — ReadModel Then / Aggregate Then"""

from behave import then


@then('AI 教練回覆應包含冷卻提示：「{message}」')
def step_impl(context, message):
    response = context.last_response
    data = response.json()
    reply = data.get("reply", "") or data.get("content", "") or data.get("message", "")
    # Also check detail for HTTPException
    if not reply and "detail" in data:
        detail = data["detail"]
        if isinstance(detail, dict):
            reply = detail.get("message", "")
        else:
            reply = str(detail)
    assert message in reply, \
        f"冷卻提示應包含「{message}」，實際回覆：{reply[:200]}"


@then('使用者 "{email}" 在接下來 30 分鐘內的 AI 教練提問應被拒絕')
def step_impl_rejected(context, email):
    from app.models.ai_cooldown import AiCooldown
    import uuid
    from datetime import datetime, timezone

    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    cooldown = db.query(AiCooldown).filter_by(user_id=user_id).order_by(
        AiCooldown.created_at.desc()
    ).first()

    assert cooldown is not None, \
        f"使用者 '{email}' 在 DB 中沒有 AiCooldown 記錄"
    assert cooldown.cooldown_until > datetime.now(timezone.utc), \
        f"冷卻時間應在未來，但 cooldown_until={cooldown.cooldown_until}"
