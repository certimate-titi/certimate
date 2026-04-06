"""When steps — 指派補考（個人化補救試卷）."""
from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 為學員 (?P<student_id>\d+) 指派補考，設定如下：')
def step_assign_remediation_setup(context, email, student_id):
    """Store remediation setup in context.memo for the next step."""
    # Table format: | 總題數 | 20 | — single row treated as headings in behave
    if len(context.table.rows) > 0:
        row = context.table[0]
        question_count = int(row["總題數"])
    else:
        # Single-row table: headings = ["總題數", "20"]
        headings = context.table.headings
        question_count = int(headings[1])
    context.memo["remediation_email"] = email
    context.memo["remediation_student_id"] = student_id
    context.memo["remediation_question_count"] = question_count


@when(r'各能力比例設定為：')
def step_set_competency_weights(context):
    """POST /api/v1/b2b/students/{student_id}/remediation-exam with weights."""
    email = context.memo["remediation_email"]
    student_id = context.memo["remediation_student_id"]
    question_count = context.memo["remediation_question_count"]

    weights = []
    for row in context.table:
        pct_str = row["比例"].replace("%", "")
        weights.append({
            "label": row["能力節點"],
            "weight": int(pct_str),
        })

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    actual_student_id = context.ids.get(str(student_id), str(student_id))
    context.last_response = context.api_client.post(
        f"/api/v1/b2b/students/{actual_student_id}/remediation-exam",
        json={
            "question_count": question_count,
            "competency_weights": weights,
        },
        headers={"Authorization": f"Bearer {token}"},
    )


use_step_matcher("parse")
