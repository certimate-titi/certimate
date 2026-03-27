from behave import when


@when('系統完成資源解析')
def step_impl(context):
    resource_id = context.ids.get("last_resource_id")
    assert resource_id is not None, "找不到 last_resource_id"

    # 使用資源擁有者的 token
    resource = context.memo.get("last_resource")
    assert resource is not None, "找不到 last_resource"
    token = context.jwt_helper.generate_token(str(resource.user_id))

    response = context.api_client.post(
        f"/api/v1/resources/{resource_id}/complete-parsing",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
