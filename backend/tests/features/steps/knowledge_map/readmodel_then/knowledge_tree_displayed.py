"""Then 右側心智圖導覽區應切換顯示 AWS SAA 的深層知識節點樹 — Read Model"""

from behave import then


@then('右側心智圖導覽區應切換顯示 AWS SAA 的深層知識節點樹（如：AWS S3、IAM）')
def knowledge_tree_displayed(context):
    response = context.memo.get("nodes_response") or context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "nodes" in data, (
        f"回應缺少 'nodes' 欄位，實際欄位: {list(data.keys())}"
    )

    nodes = data["nodes"]
    assert len(nodes) > 0, "nodes 列表不應為空"

    # Verify tree structure: at least one node should have children or depth > 0
    has_child_nodes = any(
        node.get("depth", 0) > 0 or node.get("children")
        for node in nodes
    )
    assert has_child_nodes, "知識節點樹應包含子節點（深層結構）"
