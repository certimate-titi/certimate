"""Then 科目的考古題數量應大於 0 — ReadModel Then"""

from behave import then


@then('"{subject_name}" 的考古題數量應大於 0')
def step_impl(context, subject_name):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    data = response.json()
    all_subjects = data.get("subjects", [])

    target = None
    for s in all_subjects:
        if s["name"] == subject_name:
            target = s
            break

    assert target is not None, \
        f"找不到科目 '{subject_name}'，實際: {[s['name'] for s in all_subjects]}"

    count = target.get("available_questions", 0)
    assert count > 0, \
        f"科目 '{subject_name}' 的考古題數量應大於 0，實際: {count}"
