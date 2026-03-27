"""Then 最高學歷選項應包含 — ReadModel Then"""

from behave import then


@then('最高學歷選項應包含：')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    education_options = data.get("education_options", [])

    for row in context.table:
        option = row["選項"]
        assert option in education_options, \
            f"學歷選項中找不到 '{option}'，實際: {education_options}"
