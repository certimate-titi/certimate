"""Then 錯題列表應僅包含某科目的錯題 — ReadModel Then"""

from behave import then


@then('錯題列表應僅包含 {subject_name} 科目的錯題')
def step_impl(context, subject_name):
    response = context.last_response
    data = response.json()

    wrong_answers = data.get("wrong_answers", [])
    assert len(wrong_answers) > 0, "錯題列表不應為空"

    for item in wrong_answers:
        assert item.get("subject_name") == subject_name, \
            f"預期科目 '{subject_name}'，實際 '{item.get('subject_name')}'"
