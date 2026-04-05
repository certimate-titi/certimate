"""Then 可選科目清單不應包含 — ReadModel Then"""

from behave import then


@then('可選科目清單不應包含 "{subject_name}"')
def step_impl(context, subject_name):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    data = response.json()
    all_names = [s["name"] for s in data.get("subjects", [])]
    assert subject_name not in all_names, \
        f"可選科目清單不應包含 '{subject_name}'，但實際包含: {all_names}"
