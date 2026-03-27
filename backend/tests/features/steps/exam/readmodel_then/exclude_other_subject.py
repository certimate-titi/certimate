"""Then 選題列表應排除非當前學科的資源 — ReadModel Then"""

from behave import then


@then('選題列表應排除非當前學科的資源（如 AWS 講義）')
def step_impl(context):
    response = context.last_response
    data = response.json()

    resources = data.get("resources", [])
    for r in resources:
        assert "AWS" not in r.get("name", ""), (
            f"不應包含 AWS 相關資源，但找到 '{r.get('name')}'"
        )
