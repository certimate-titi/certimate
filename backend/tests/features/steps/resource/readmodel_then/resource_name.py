"""Then assertion — resource name check."""

from behave import then


@then('新建立資源的 name 應為 "{expected_name}"')
def step_assert_resource_name(context, expected_name):
    response = context.last_response
    data = response.json()
    actual_name = data.get("name") or data.get("resource", {}).get("name")
    assert actual_name is not None, f"回應中找不到 name 欄位: {data}"
    assert actual_name == expected_name, (
        f"資源 name 應為 {expected_name!r}，實際為 {actual_name!r}"
    )
