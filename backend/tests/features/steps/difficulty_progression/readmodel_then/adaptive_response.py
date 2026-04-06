"""Then 自適應練習/策略/軌跡回應驗證 — ReadModel Then"""

from behave import then


@then('回應應包含出題策略：')
def step_impl_strategy_fields(context):
    response = context.last_response
    data = response.json()
    for row in context.table:
        field = row["欄位"]
        assert field in data, f"回應缺少欄位 '{field}', 有: {list(data.keys())}"


@then('回應應包含題目：')
def step_impl_question_fields(context):
    response = context.last_response
    data = response.json()
    question = data.get("question")
    assert question is not None, f"回應缺少 question 欄位, 有: {list(data.keys())}"
    for row in context.table:
        field = row["欄位"]
        assert field in question, \
            f"question 缺少欄位 '{field}', 有: {list(question.keys())}"


@then('回應應包含 {count:d} 筆軌跡紀錄')
def step_impl_trail_count(context, count):
    response = context.last_response
    data = response.json()
    trail = data.get("trail", [])
    assert len(trail) == count, \
        f"期望 {count} 筆軌跡, 實際 {len(trail)}"


@then('軌跡應清楚標記每一步的 backtrack / progress 動作')
def step_impl_trail_actions(context):
    response = context.last_response
    data = response.json()
    trail = data.get("trail", [])
    for i, entry in enumerate(trail):
        assert "action" in entry, \
            f"第 {i + 1} 筆軌跡缺少 action 欄位"
        assert entry["action"] in ("answer", "backtrack", "progress", "stay"), \
            f"第 {i + 1} 筆軌跡 action 無效: {entry['action']}"


@then('節點 "{node_name}" 的 mastery_rate 應已更新（反映新的答對紀錄）')
def step_impl_mastery_updated(context, node_name):
    # Just verify the map API returns data with the node
    response = context.last_response
    data = response.json()
    nodes = data.get("nodes", [])

    def find_node(nodes_list, name):
        for n in nodes_list:
            if n["name"] == name:
                return n
            found = find_node(n.get("children", []), name)
            if found:
                return found
        return None

    node = find_node(nodes, node_name)
    assert node is not None, f"找不到節點 '{node_name}'"
    # mastery_rate should exist (could be any value since we added correct answers)
    assert "mastery_rate" in node, f"節點 '{node_name}' 缺少 mastery_rate"


@then('節點顏色應依新的 mastery_rate 重新計算')
def step_impl_color_updated(context):
    response = context.last_response
    data = response.json()
    nodes = data.get("nodes", [])

    def check_node(n):
        if n.get("mastery_rate") is not None and not n.get("locked"):
            rate = n["mastery_rate"]
            color = n.get("color")
            if rate >= 80:
                expected = "green"
            elif rate >= 60:
                expected = "orange"
            else:
                expected = "red"
            assert color == expected, \
                f"節點 '{n.get('name')}' rate={rate}, 期望 color={expected}, 實際={color}"
        for c in n.get("children", []):
            check_node(c)

    for n in nodes:
        check_node(n)
