"""Then 錯題地圖回應驗證 — ReadModel Then"""

from behave import then


@then('回應應為帶有 mastery 資訊的知識樹 JSON：')
def step_impl_has_nodes(context):
    response = context.last_response
    data = response.json()
    assert "nodes" in data, f"回應缺少 nodes 欄位, 實際: {list(data.keys())}"
    assert isinstance(data["nodes"], list), "nodes 應為 list"
    assert len(data["nodes"]) > 0, "nodes 不應為空"


@then('每個節點應包含：')
def step_impl_node_fields(context):
    response = context.last_response
    data = response.json()
    nodes = data["nodes"]

    expected_fields = set()
    for row in context.table:
        expected_fields.add(row["欄位"])

    def check_node(node, path="root"):
        for field in expected_fields:
            assert field in node, \
                f"節點 {path}/{node.get('name', '?')} 缺少欄位 '{field}', 有: {list(node.keys())}"
        for child in node.get("children", []):
            check_node(child, f"{path}/{node.get('name', '?')}")

    for n in nodes:
        check_node(n)


@then('父節點 "{node_name}" 的 mastery_rate 應為子節點的加權平均')
def step_impl_weighted_avg(context, node_name):
    response = context.last_response
    data = response.json()

    def find_node(nodes, name):
        for n in nodes:
            if n["name"] == name:
                return n
            found = find_node(n.get("children", []), name)
            if found:
                return found
        return None

    node = find_node(data["nodes"], node_name)
    assert node is not None, f"找不到節點 '{node_name}'"
    assert node.get("mastery_rate") is not None, \
        f"節點 '{node_name}' 的 mastery_rate 為 null"

    # Check that it's a reasonable average of children
    children = node.get("children", [])
    if children:
        child_rates = [c["mastery_rate"] for c in children
                       if c.get("mastery_rate") is not None]
        if child_rates:
            expected_avg = sum(child_rates) / len(child_rates)
            actual = node["mastery_rate"]
            assert abs(actual - expected_avg) < 5, \
                f"節點 '{node_name}' 的 mastery_rate={actual}, 期望接近 {expected_avg}"


@then('父節點 "{node_name}" 的 color 應依照計算後的 mastery_rate 決定')
def step_impl_parent_color(context, node_name):
    response = context.last_response
    data = response.json()

    def find_node(nodes, name):
        for n in nodes:
            if n["name"] == name:
                return n
            found = find_node(n.get("children", []), name)
            if found:
                return found
        return None

    node = find_node(data["nodes"], node_name)
    assert node is not None, f"找不到節點 '{node_name}'"

    rate = node.get("mastery_rate")
    color = node.get("color")
    assert color is not None, f"節點 '{node_name}' 的 color 為 null"

    if rate is not None:
        if rate >= 80:
            expected = "green"
        elif rate >= 60:
            expected = "orange"
        else:
            expected = "red"
        assert color == expected, \
            f"節點 '{node_name}' rate={rate}, 期望 color={expected}, 實際={color}"
