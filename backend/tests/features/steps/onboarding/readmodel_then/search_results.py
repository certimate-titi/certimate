"""Then 搜尋結果應包含 — ReadModel Then"""

from behave import then


@then('搜尋結果應包含 "{subject}"')
def step_impl(context, subject):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    subjects = [s.get("name", "") for s in data.get("subjects", [])]
    assert subject in subjects, \
        f"搜尋結果中找不到 '{subject}'，實際: {subjects}"
