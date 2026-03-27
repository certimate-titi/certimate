"""Then 年齡選擇範圍 — ReadModel Then"""

from behave import then


@then('年齡選擇範圍應為 {min_age:d} 至 {max_age:d} 歲')
def step_impl(context, min_age, max_age):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    age_config = data.get("age_range", {})
    assert age_config.get("min") == min_age, \
        f"預期最小年齡 {min_age}，實際 {age_config.get('min')}"
    assert age_config.get("max") == max_age, \
        f"預期最大年齡 {max_age}，實際 {age_config.get('max')}"
