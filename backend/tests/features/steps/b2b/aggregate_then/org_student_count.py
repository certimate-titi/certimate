"""Then step — 機構學生數量驗證."""
from behave import then


@then('機構 {inst_id:d} 的學生數量應為 {expected:d}')
def step_org_student_count(context, inst_id, expected):
    """Verify the number of students in an institution."""

    from app.models.user import User
    count = context.db_session.query(User).filter(
        User.org_id.isnot(None),
        User.role == "student",
    ).count()
    assert count == expected, f"Expected {expected} students, got {count}"
