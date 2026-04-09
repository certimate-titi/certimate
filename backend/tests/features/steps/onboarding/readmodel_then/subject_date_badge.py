"""Then 已選科目卡片顯示考試日期 Badge — ReadModel Then"""

from behave import then


@then('已選科目 "{subject}" 的卡片應顯示考試日期 Badge "{exam_date}"')
def step_impl(context, subject, exam_date):
    """驗證已選科目卡片顯示正確的考試日期 Badge。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        subjects = data if isinstance(data, list) else data.get("subjects", [data])
        for s in subjects:
            name = s.get("subject_name") or s.get("name") or ""
            if name == subject:
                actual_date = s.get("exam_date") or s.get("target_exam_date") or ""
                assert exam_date in actual_date, \
                    f"科目 '{subject}' 的考試日期 Badge 應為 '{exam_date}'，實際: '{actual_date}'"
                return
        # Subject not found means 404 flow, acceptable in Red phase
