"""Then step: 橫幅不應包含任何 Email、姓名或使用者 ID"""

import re

from behave import then


@then('橫幅不應包含任何 Email、姓名或使用者 ID')
def step_impl(context):
    data = context.last_response.json()
    banner = data.get("banner", {})
    message = banner.get("message", "")

    # Check no email pattern
    assert not re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', message), \
        f"Banner contains email: {message}"

    # Check no UUID pattern
    assert not re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', message), \
        f"Banner contains UUID: {message}"
