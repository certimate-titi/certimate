"""Then 各科目的考試日期與自評程度均應正確顯示 — ReadModel Then"""

from behave import then


@then('各科目的考試日期與自評程度均應正確顯示')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    subjects = data.get("subjects", [])
    for s in subjects:
        assert "exam_date" in s, f"科目缺少 exam_date: {s}"
        assert "self_assessed_level" in s, f"科目缺少 self_assessed_level: {s}"
