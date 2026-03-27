from behave import then


@then('新建立的資源類型應為 "{resource_type}"')
def step_impl(context, resource_type):
    response = context.last_response
    data = response.json()
    actual_type = data.get("type") or data.get("resource", {}).get("type")
    assert actual_type is not None, f"回應中找不到 type 欄位: {data}"
    assert actual_type == resource_type, \
        f"資源類型應為 '{resource_type}'，實際為 '{actual_type}'"
