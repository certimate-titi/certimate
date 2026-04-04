"""Then 回應應包含學員能力列表 — ReadModel Then"""

from behave import then, use_step_matcher

use_step_matcher("re")


@then(r'回應應包含學員 ID (?P<student_id>\d+) 的能力列表')
def step_impl(context, student_id):
    response = context.last_response
    data = response.json()
    assert "competencies" in data, \
        f"回應中找不到 competencies 欄位，回應: {list(data.keys())}"

    # student_id from feature is a numeric key, actual ID is a UUID
    actual_uuid = context.ids.get(student_id, student_id)
    response_id = str(data.get("student_id", ""))
    assert response_id == actual_uuid or response_id == student_id, \
        f"預期學員 ID {actual_uuid}，實際 {response_id}"


use_step_matcher("parse")


@then('每個能力節點應包含：')
def step_impl_fields(context):
    response = context.last_response
    data = response.json()
    competencies = data.get("competencies", [])

    required_fields = [row["欄位"] for row in context.table]

    if len(competencies) > 0:
        for c in competencies:
            for field in required_fields:
                assert field in c, \
                    f"能力節點中找不到欄位 '{field}'，實際: {list(c.keys())}"
