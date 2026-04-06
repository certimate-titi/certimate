"""Then 訂閱限制 — 節點 locked 狀態驗證 — ReadModel Then"""

from behave import then


@then('回應中 depth > {max_depth:d} 的節點應標記為 locked: true')
def step_impl_locked(context, max_depth):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    data = response.json()
    tree = data.get("tree", data.get("children", data))

    def _check_locked(nodes):
        for node in nodes:
            depth = node.get("depth", 0)
            locked = node.get("locked", False)
            if depth > max_depth:
                assert locked is True, \
                    f"節點 '{node.get('name')}' (depth={depth}) 應為 locked=true"
            children = node.get("children", [])
            if children:
                _check_locked(children)

    if isinstance(tree, list):
        _check_locked(tree)
    else:
        _check_locked([tree])


@then('所有節點 locked 應為 false')
def step_impl_unlocked(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    data = response.json()
    tree = data.get("tree", data.get("children", data))

    def _check_unlocked(nodes):
        for node in nodes:
            locked = node.get("locked", False)
            assert locked is False, \
                f"節點 '{node.get('name')}' 應為 locked=false，實際為 locked={locked}"
            children = node.get("children", [])
            if children:
                _check_unlocked(children)

    if isinstance(tree, list):
        _check_unlocked(tree)
    else:
        _check_unlocked([tree])
