"""Then 回應包含 nodes 陣列 — Read Model

驗證 /knowledge-map/subjects/{id}/nodes 回應 200 且含 nodes 陣列。
"""

from behave import then


@then('回應包含 nodes 陣列')
def step_impl(context):
    """驗證回應 HTTP 200 且 body 含 nodes 陣列欄位。"""
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "nodes" in data, (
        f"回應 body 應包含 'nodes' 欄位，實際欄位：{list(data.keys())}"
    )
    assert isinstance(data["nodes"], list), (
        f"'nodes' 應為陣列，實際型別：{type(data['nodes'])}"
    )
