"""Given 使用者本月基礎教練剩餘額度 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 本月基礎教練剩餘額度為 {count:d}')
def step_impl(context, email, count):
    """設定使用者的本月基礎教練剩餘額度。"""
    from app.models.user import User
    from app.models.ai_cooldown import AiCooldown
    import uuid
    from datetime import datetime, timezone

    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    # Store quota in memo for step reference
    context.memo[f"basic_coach_quota_{email}"] = count
    context.memo["current_user_email"] = email
