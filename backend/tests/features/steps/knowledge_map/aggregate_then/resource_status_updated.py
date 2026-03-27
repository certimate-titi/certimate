from behave import then
from app.models.resource import Resource


@then('資源狀態應更新為 "{status}"')
def step_impl(context, status):
    # 先驗證 API 回應成功
    response = context.last_response
    assert response is not None, "沒有 HTTP 回應"
    assert response.status_code in [200, 201], \
        f"API 回應失敗: {response.status_code} - {response.text}"

    # 從 DB 查詢驗證資源狀態
    db = context.db_session
    resource_id = context.ids.get("last_resource_id")
    assert resource_id is not None, "找不到 last_resource_id"

    db.expire_all()
    resource = db.query(Resource).filter_by(id=resource_id).first()
    assert resource is not None, f"找不到 resource_id={resource_id}"
    actual_status = resource.status.value if hasattr(resource.status, 'value') else resource.status
    assert actual_status == status, \
        f"資源狀態應為 '{status}'，實際為 '{actual_status}'"
