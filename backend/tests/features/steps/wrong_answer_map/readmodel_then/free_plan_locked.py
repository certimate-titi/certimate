"""Then FREE 用戶錯題地圖權限驗證 — ReadModel Then"""

from behave import then


@then('depth == 1 的節點應包含 mastery_rate 與 color')
def step_impl_depth1(context):
    response = context.last_response
    data = response.json()
    nodes = data.get("nodes", [])

    for node in nodes:
        if node.get("depth") == 1:
            assert "mastery_rate" in node, \
                f"depth=1 節點 '{node.get('name')}' 缺少 mastery_rate"
            assert "color" in node, \
                f"depth=1 節點 '{node.get('name')}' 缺少 color"


@then('depth > 1 的節點應標記為 locked: true，mastery_rate 為 null')
def step_impl_locked(context):
    response = context.last_response
    data = response.json()
    nodes = data.get("nodes", [])

    def check_locked(node_list):
        for node in node_list:
            if node.get("depth", 0) > 1:
                assert node.get("locked") is True, \
                    f"depth>1 節點 '{node.get('name')}' 應為 locked=true"
                assert node.get("mastery_rate") is None, \
                    f"depth>1 節點 '{node.get('name')}' 的 mastery_rate 應為 null, 實際={node.get('mastery_rate')}"
            check_locked(node.get("children", []))

    check_locked(nodes)
