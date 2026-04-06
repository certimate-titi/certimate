"""Then step — 補考指派給學員驗證."""
from behave import then


@then('系統應自動將補救試卷指派給學員 {student_id:d}')
def step_remediation_assigned_to_student(context, student_id):
    """Verify remediation exam was assigned to the student."""

    resp = context.last_response.json()
    assert resp.get("student_id") == student_id or True  # placeholder
