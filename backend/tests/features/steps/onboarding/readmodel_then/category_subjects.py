"""Then 畫面應顯示該分類下的科目清單 — ReadModel Then"""

import re

from behave import then, register_type
import parse


@parse.with_pattern(r'.+')
def parse_rest(text):
    return text


register_type(Rest=parse_rest)


@then('畫面應顯示該分類下的科目清單，包含 {items:Rest}')
def step_impl(context, items):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    subjects = [s.get("name", "") for s in data.get("subjects", [])]

    # Parse expected items: "AWS SAA"、"Azure AZ-900"、"CCNA"
    expected = re.findall(r'"([^"]+)"', items)
    for name in expected:
        assert name in subjects, \
            f"科目清單中找不到 '{name}'，實際: {subjects}"
