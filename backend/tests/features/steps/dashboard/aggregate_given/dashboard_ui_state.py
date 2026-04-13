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
    """建立使用者科目複習排程（在 DB 中建立 NodeMastery + KnowledgeNode）。"""
    from app.models.user import User
    from app.models.subject import Subject
    from app.models.knowledge_node import KnowledgeNode
    from app.models.node_mastery import NodeMastery
    from datetime import datetime, timezone

    db = context.db_session
    user = db.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    subj = db.query(Subject).filter(Subject.name == subject).first()
    assert subj, f"找不到科目 {subject}"

    node_counter = 0
    for row in context.table:
        date_str = row["日期"]
        count = int(row["複習項目數"])
        review_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # 為每個複習項目建立一個 KnowledgeNode + NodeMastery
        for i in range(count):
            node_counter += 1
            node = KnowledgeNode(
                name=f"複習節點_{date_str}_{i+1}",
                subject_id=subj.id,
                depth=1,
            )
            db.add(node)
            db.flush()

            mastery = NodeMastery(
                user_id=user.id,
                node_id=node.id,
                next_review_at=review_date,
                base_mastery=0.5,
                ease_factor=2.5,
                status="PENDING",
            )
            db.add(mastery)

    db.commit()
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
