"""Then 心智圖應顯示指定科目的知識節點 — ReadModel Then"""

from behave import then


@then('心智圖應顯示 {subject} 的知識節點：')
def step_impl(context, subject):
    response = context.last_response
    data = response.json()

    nodes = data.get("nodes", [])
    expected_nodes = {}
    for row in context.table:
        expected_nodes[row['節點 ID']] = row['名稱']

    actual_names = {str(n.get("node_id", n.get("id", ""))): n.get("name", "") for n in nodes}

    for node_id, name in expected_nodes.items():
        found = False
        for actual_name in actual_names.values():
            if actual_name == name:
                found = True
                break
        assert found, f"找不到節點 '{name}' (ID: {node_id}) 在回應中"
