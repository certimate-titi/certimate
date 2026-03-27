from behave import then


@then('新建立的資源狀態應為 "{status}"')
def step_impl(context, status):
    response = context.last_response
    data = response.json()
    actual_status = data.get("status") or data.get("resource", {}).get("status")
    assert actual_status is not None, f"回應中找不到 status 欄位: {data}"
    assert actual_status == status, \
        f"資源狀態應為 '{status}'，實際為 '{actual_status}'"
