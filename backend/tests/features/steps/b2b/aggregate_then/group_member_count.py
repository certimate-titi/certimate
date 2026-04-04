"""Then 群組的成員數應為 N — Aggregate Then"""

from behave import then

from app.models.student_group import StudentGroup, StudentGroupMember


@then('群組 "{group_name}" 的成員數應為 {count:d}')
def step_impl(context, group_name, count):
    db = context.db_session
    group = db.query(StudentGroup).filter_by(name=group_name).first()
    assert group is not None, f"找不到群組 '{group_name}'"

    actual = db.query(StudentGroupMember).filter_by(group_id=group.id).count()
    assert actual == count, \
        f"預期群組 '{group_name}' 有 {count} 位成員，實際為 {actual}"
