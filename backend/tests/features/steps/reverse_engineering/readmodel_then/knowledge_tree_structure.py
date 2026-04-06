"""Then 知識樹結構驗證 — ReadModel Then"""

from behave import then


@then('知識樹應包含至少 {count:d} 層結構：')
def step_impl(context, count):
    response = context.last_response
    assert response.status_code in [200, 201], \
        f"預期成功，實際 {response.status_code}: {response.text}"

    data = response.json()
    tree = data.get("tree", data.get("children", data))

    # Calculate max depth of tree
    def _max_depth(nodes, current=1):
        if not nodes:
            return current - 1
        return max(_max_depth(n.get("children", []), current + 1) for n in nodes)

    if isinstance(tree, list):
        max_d = _max_depth(tree)
    else:
        max_d = _max_depth([tree])

    assert max_d >= count, \
        f"預期知識樹至少 {count} 層，實際最大深度為 {max_d}"


@then('每個知識節點應包含：')
def step_impl_node_fields(context):
    response = context.last_response
    data = response.json()
    tree = data.get("tree", data.get("children", data))

    # Collect expected fields from DataTable
    expected_fields = [row["欄位"] for row in context.table]

    def _check_nodes(nodes):
        for node in nodes:
            for field in expected_fields:
                assert field in node, \
                    f"節點 '{node.get('name', '?')}' 缺少欄位 '{field}'"
            children = node.get("children", [])
            if children:
                _check_nodes(children)

    if isinstance(tree, list):
        _check_nodes(tree)
    else:
        _check_nodes([tree])
