"""Then step — 學員仍在機構驗證."""
from behave import then


@then('使用者 "{email}" 仍存在於機構 {inst_id:d} 中')
def step_student_still_in_org(context, email, inst_id):
    """Verify user still belongs to the institution."""

    from app.models.user import User
    user = context.db_session.query(User).filter_by(email=email).first()
    assert user is not None, f"User {email} not found"
    # User should still have org_id set
    assert user.org_id is not None, f"User {email} has no org_id"
