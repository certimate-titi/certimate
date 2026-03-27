"""Then 知識點分析應包含 / 節點顏色標示 — ReadModel Then"""

from behave import then


@then('知識點分析應包含：')
def step_impl(context):
    response = context.last_response
    data = response.json()
    nodes = data.get("nodes", [])

    for row in context.table:
        name = row["節點名稱"]
        expected_rate = row["答對率"]
        expected_color = row["顏色標示"]

        found = None
        for n in nodes:
            if n.get("name") == name:
                found = n
                break

        assert found is not None, \
            f"找不到節點 '{name}'，回傳節點: {[n.get('name') for n in nodes]}"
        assert found.get("accuracy_rate") == expected_rate, \
            f"節點 '{name}' 答對率應為 '{expected_rate}'，實際為 '{found.get('accuracy_rate')}'"
        assert found.get("color") == expected_color, \
            f"節點 '{name}' 顏色應為 '{expected_color}'，實際為 '{found.get('color')}'"


@then('節點 "{node_name}" 的顏色標示應為 "{color}"')
def step_node_color(context, node_name, color):
    response = context.last_response
    data = response.json()
    nodes = data.get("nodes", [])

    found = None
    for n in nodes:
        if n.get("name") == node_name:
            found = n
            break

    assert found is not None, \
        f"找不到節點 '{node_name}'，回傳節點: {[n.get('name') for n in nodes]}"
    assert found.get("color") == color, \
        f"節點 '{node_name}' 顏色應為 '{color}'，實際為 '{found.get('color')}'"
