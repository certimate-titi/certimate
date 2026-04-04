"""Then 預警清單中包含學員 / 學員資料包含 — ReadModel Then"""

from behave import then


@then('回應中應包含學員 "{email}"')
def step_impl(context, email):
    response = context.last_response
    data = response.json()
    students = data.get("warnings", data.get("students", []))

    emails = [s.get("email", "") for s in students]
    assert email in emails, \
        f"預期包含學員 '{email}'，實際學員列表: {emails}"

    # Store the matched student for next step
    for s in students:
        if s.get("email") == email:
            context.memo["last_warning_student"] = s
            break


@then('該學員資料應包含：')
def step_impl_fields(context):
    student = context.memo.get("last_warning_student")
    if not student:
        response = context.last_response
        data = response.json()
        students = data.get("warnings", data.get("students", []))
        assert len(students) > 0, "預警清單為空"
        student = students[0]

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]
        actual = student.get(field)
        assert actual is not None, \
            f"學員資料中找不到欄位 '{field}'，實際: {list(student.keys())}"

        # For student_id, resolve from context.ids
        if field == "student_id":
            actual_uuid = context.ids.get(expected, expected)
            assert str(actual) == str(actual_uuid) or str(expected) in str(actual), \
                f"欄位 '{field}': 預期 '{expected}'（UUID: {actual_uuid}），實際 '{actual}'"
        else:
            assert str(expected) in str(actual), \
                f"欄位 '{field}': 預期 '{expected}'，實際 '{actual}'"
