"""Then 回應的 resources 清單不包含 / 包含特定 resource_id — Read Model（Issue #74）"""

from behave import then


@then('回應的 "resources" 清單不包含 "{resource_name}" 的 resource_id')
def step_resources_not_contain(context, resource_name):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )
    data = response.json()
    resources = data.get("resources", [])

    if resource_name not in context.ids:
        raise KeyError(f"找不到資源 '{resource_name}' 的 ID（尚未建立？）")

    excluded_id = context.ids[resource_name]
    resource_ids_in_response = [str(r.get("id", "")) for r in resources]

    assert excluded_id not in resource_ids_in_response, (
        f"資源 '{resource_name}' ({excluded_id}) 不應出現在 resources 清單中，"
        f"但實際回應包含它。回應 resource_ids: {resource_ids_in_response}"
    )


@then('回應的 "resources" 清單包含 "{resource_name}" 的 resource_id')
def step_resources_contain(context, resource_name):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )
    data = response.json()
    resources = data.get("resources", [])

    if resource_name not in context.ids:
        raise KeyError(f"找不到資源 '{resource_name}' 的 ID（尚未建立？）")

    expected_id = context.ids[resource_name]
    resource_ids_in_response = [str(r.get("id", "")) for r in resources]

    assert expected_id in resource_ids_in_response, (
        f"資源 '{resource_name}' ({expected_id}) 應出現在 resources 清單中，"
        f"但實際回應未包含它。回應 resource_ids: {resource_ids_in_response}"
    )
