"""Then step — 群組不存在驗證."""
from behave import then


@then('機構 {inst_id:d} 不再包含群組 "{group_name}"')
def step_group_not_exists(context, inst_id, group_name):
    """Verify the group no longer exists in the institution."""

    from app.models.student_group import StudentGroup
    group = context.db_session.query(StudentGroup).filter_by(
        name=group_name,
    ).first()
    assert group is None, f"Group '{group_name}' still exists"
