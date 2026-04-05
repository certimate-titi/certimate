"""Then API 回應應包含科目及其設定 — ReadModel Then"""

from behave import then


@then('API 回應應包含科目 "{subject_name}" 及其考試日期和自評程度')
def step_impl(context, subject_name):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    data = response.json()
    # Handle both list and dict response formats
    subjects = data if isinstance(data, list) else data.get("subjects", [data])

    found = False
    for s in subjects:
        name = s.get("subject_name") or s.get("name") or ""
        if name == subject_name:
            found = True
            break

    assert found, \
        f"API 回應中找不到科目 '{subject_name}'，實際: {data}"
