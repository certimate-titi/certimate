"""Then 頁面應載入與 AWS SAA 關聯的學習資源列表 — Read Model"""

from behave import then


@then('頁面應載入與 AWS SAA 關聯的學習資源列表')
def resource_list_loaded(context):
    # 讀取切換學科時發出的「資源列表」請求回應（由 switch_subject step 存入）
    response = context.memo.get("resources_response") or context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "resources" in data, (
        f"回應缺少 'resources' 欄位，實際欄位: {list(data.keys())}"
    )
    assert len(data["resources"]) > 0, "resources 列表不應為空"
