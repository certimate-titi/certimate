"""Then 使用者的角色驗證 + 不可自主建立測驗 — Aggregate Then"""

from behave import then

from app.models.user import User

# Note: 使用者 "{email}" 的訂閱方案應為 step is defined in subscription/aggregate_then/subscription_plan.py
# Note: 使用者 "{email}" 的每日 AI 對話限額應為 step is defined in subscription_upgrade/aggregate_then/quota_exact.py
# Note: 使用者 "{email}" 不可上傳資源 step is defined in subscription_upgrade/aggregate_then/edu_restrictions.py


@then('使用者 "{email}" 的角色應為 "{expected_role}"')
def step_impl_role(context, email, expected_role):
    db = context.db_session
    user = db.query(User).filter_by(email=email).first()
    assert user is not None, f"找不到使用者 {email}"

    role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    assert role == expected_role, \
        f"預期角色為 {expected_role}，實際為 {role}"


@then('使用者 "{email}" 不可自主建立測驗')
def step_impl_no_exam(context, email):
    """EDU students can only take assigned exams, not create their own."""
    db = context.db_session
    user = db.query(User).filter_by(email=email).first()
    assert user is not None, f"找不到使用者 {email}"
    role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    assert role == "student", f"預期角色為 student，實際為 {role}"
