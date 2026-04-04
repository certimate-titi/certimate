"""Then 機構所有 EDU 學生的訂閱方案應自動降級為 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User


@then('機構 {inst_id:d} 所有 EDU 學生的訂閱方案應自動降級為 "{expected_plan}"')
def step_impl(context, inst_id, expected_plan):
    db = context.db_session
    db.expire_all()
    inst_uuid = uuid.UUID(int=inst_id)

    students = db.query(User).filter_by(org_id=inst_uuid).all()
    assert len(students) > 0, f"機構 {inst_id} 沒有學生"

    expected_db = "FREE" if expected_plan == "FREE" else expected_plan

    for student in students:
        actual = student.subscription_plan.value if hasattr(student.subscription_plan, 'value') else str(student.subscription_plan)
        assert actual == expected_db, (
            f"學生 '{student.email}' 預期降級至 '{expected_db}'，實際 '{actual}'"
        )
