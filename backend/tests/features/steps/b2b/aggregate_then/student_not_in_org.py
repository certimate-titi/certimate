"""Then step — 學員不在機構驗證."""
from behave import then


@then('使用者 "{email}" 不再屬於機構 {inst_id:d}')
def step_student_not_in_org(context, email, inst_id):
    """Verify user no longer belongs to the institution."""

    from app.models.user import User
    user = context.db_session.query(User).filter_by(email=email).first()
    assert user is not None, f"User {email} not found"
    assert user.org_id is None, f"User {email} still has org_id"
