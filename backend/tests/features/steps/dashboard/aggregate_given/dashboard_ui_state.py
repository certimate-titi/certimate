"""Given 個人儀表板 UI 前置狀態 — Aggregate Given"""

import uuid

from behave import given


@given('使用者 "{email}" 目前連勝為 {days:d} 天')
def step_impl_streak_days(context, email, days):
    """設定使用者目前連勝天數。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if user and hasattr(user, "streak_days"):
        user.streak_days = days
        context.db_session.commit()
    context.memo["current_streak"] = days
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 有一個類型為 "{task_type}" 的任務「{task_name}」，狀態為 "{status}"')
def step_impl_user_has_quest(context, email, task_type, task_name, status):
    """記錄使用者有特定類型任務（UI 前置狀態）。"""
    context.memo["quest_type"] = task_type
    context.memo["quest_name"] = task_name
    context.memo["quest_status"] = status
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 有一筆上傳失敗的資源，ID 為 "{resource_id}"')
def step_impl_failed_resource(context, email, resource_id):
    """記錄使用者有上傳失敗的資源（UI 前置狀態）。"""
    context.memo["failed_resource_id"] = resource_id
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 在 "{subject}" 科目有以下能力分布：')
def step_impl_ability_distribution(context, email, subject):
    """記錄使用者科目能力分布（用於雷達圖）。"""
    distribution = []
    for row in context.table:
        distribution.append({
            "domain": row["領域"],
            "strength": int(row["強度"]),
        })
    context.memo["radar_distribution"] = distribution
    context.memo["radar_subject"] = subject
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 在 "{subject}" 科目有以下複習排程：')
def step_impl_review_schedule(context, email, subject):
    """記錄使用者科目複習排程（用於艾賓浩斯月曆）。"""
    schedules = []
    for row in context.table:
        schedules.append({
            "date": row["日期"],
            "count": int(row["複習項目數"]),
        })
    context.memo["review_schedule"] = schedules
    context.memo["review_subject"] = subject
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 的訂閱方案為 "{plan}"')
def step_impl_user_subscription_plan(context, email, plan):
    """設定使用者訂閱方案（以 email 為識別）。"""
    from app.models.user import User, SubscriptionPlan
    _PLAN_MAP = {
        "FREE": SubscriptionPlan.FREE,
        "PRO_199": SubscriptionPlan.PRO,
        "PRO_PLUS_399": SubscriptionPlan.PRO_PLUS,
        "ULTRA_1599": SubscriptionPlan.ULTRA,
    }
    user = context.db_session.query(User).filter(User.email == email).first()
    if user:
        plan_enum = _PLAN_MAP.get(plan)
        if plan_enum:
            user.subscription_plan = plan_enum
            context.db_session.commit()
    context.memo["current_user_email"] = email
