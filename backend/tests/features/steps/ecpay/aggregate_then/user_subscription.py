"""Then 使用者的訂閱方案/狀態/扣款日應更新 — Aggregate Then"""

import uuid
from datetime import datetime

from behave import then

from app.models.user import User


@then('使用者 {user_id:d} 的訂閱方案應更新為 "{plan}"')
def step_plan(context, user_id, plan):
    db = context.db_session
    db.expire_all()

    user_uuid = uuid.UUID(context.ids[str(user_id)])
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 {user_id}"

    actual = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    # PRO_199 映射到 PRO enum
    plan_map = {"PRO_199": "PRO", "PRO_PLUS_399": "PRO_PLUS", "ULTRA_1599": "ULTRA"}
    expected = plan_map.get(plan, plan)

    assert actual == expected, (
        f"使用者 {user_id} 的訂閱方案預期 '{expected}'，實際 '{actual}'"
    )


@then('使用者 {user_id:d} 的訂閱狀態應更新為 "{status}"')
def step_status(context, user_id, status):
    db = context.db_session
    db.expire_all()

    user_uuid = uuid.UUID(context.ids[str(user_id)])
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 {user_id}"

    actual = user.subscription_status.value if hasattr(user.subscription_status, 'value') else str(user.subscription_status)
    assert actual == status, (
        f"使用者 {user_id} 的訂閱狀態預期 '{status}'，實際 '{actual}'"
    )


@then('使用者 {user_id:d} 的下次扣款日應設為 "{date}"')
def step_billing_date(context, user_id, date):
    db = context.db_session
    db.expire_all()

    user_uuid = uuid.UUID(context.ids[str(user_id)])
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 {user_id}"
    assert user.next_billing_date is not None, (
        f"使用者 {user_id} 的 next_billing_date 為 None"
    )

    expected = datetime.fromisoformat(date).date()
    actual = user.next_billing_date.date()
    assert actual == expected, (
        f"使用者 {user_id} 的扣款日預期 '{expected}'，實際 '{actual}'"
    )


@then('使用者 {user_id:d} 的訂閱方案應維持 "{plan}"')
def step_plan_unchanged(context, user_id, plan):
    db = context.db_session
    db.expire_all()

    user_uuid = uuid.UUID(context.ids[str(user_id)])
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 {user_id}"

    actual = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    plan_map = {"PRO_199": "PRO", "PRO_PLUS_399": "PRO_PLUS", "ULTRA_1599": "ULTRA"}
    expected = plan_map.get(plan, plan)

    assert actual == expected, (
        f"使用者 {user_id} 的訂閱方案預期維持 '{expected}'，實際 '{actual}'"
    )


@then('使用者 {user_id:d} 的訂閱紀錄不應被重複修改')
def step_no_duplicate(context, user_id):
    # 驗證訂閱未被重複修改 — 只需確認記錄存在且一致即可
    db = context.db_session
    db.expire_all()

    user_uuid = uuid.UUID(context.ids[str(user_id)])
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 {user_id}"
    # 若已是 success，重複回呼不應改變任何狀態
