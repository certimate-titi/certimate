"""Canvas BDD — Then response assertions."""

from behave import then


def _body(context):
    assert context.last_response is not None, "無 last_response"
    return context.last_response.json()


@then('Canvas 回應節點數為 {n:d}')
def step_node_count(context, n):
    body = _body(context)
    nodes = body.get("nodes", [])
    assert len(nodes) == n, f"預期 {n} 節點，實際 {len(nodes)}: {nodes}"


@then('Canvas 節點 "{name}" 的 depth 為 {depth:d}')
def step_node_depth(context, name, depth):
    body = _body(context)
    node = next((n for n in body.get("nodes", []) if n["name"] == name), None)
    assert node is not None, f"找不到節點 {name}"
    assert node["depth"] == depth, f"預期 depth={depth}，實際 {node['depth']}"


@then('Canvas 節點 "{name}" 的 mastery_rate 介於 {low:d} 到 {high:d}')
def step_node_mastery_range(context, name, low, high):
    body = _body(context)
    node = next((n for n in body.get("nodes", []) if n["name"] == name), None)
    assert node is not None, f"找不到節點 {name}"
    rate = node["mastery_rate"]
    assert low <= rate <= high, f"mastery_rate {rate} 不在 [{low}, {high}]"


@then('Canvas 父節點資訊包含 parent_name="{name}" 與 parent_depth={depth:d}')
def step_parent_info(context, name, depth):
    body = _body(context)
    assert body.get("parent_name") == name, f"parent_name: {body.get('parent_name')}"
    assert body.get("parent_depth") == depth, f"parent_depth: {body.get('parent_depth')}"


@then('Canvas 節點 "{name}" 的 has_children 為 {flag}')
def step_has_children(context, name, flag):
    body = _body(context)
    node = next((n for n in body.get("nodes", []) if n["name"] == name), None)
    assert node is not None, f"找不到節點 {name}"
    expected = flag.lower() == "true"
    assert node["has_children"] is expected, f"has_children: {node['has_children']}"


@then('Canvas 回應 empty_reason 為 "{reason}"')
def step_empty_reason(context, reason):
    body = _body(context)
    assert body.get("empty_reason") == reason, f"empty_reason: {body.get('empty_reason')}"


@then('Canvas 錯誤訊息包含 "{fragment}"')
def step_error_message_contains(context, fragment):
    body = _body(context)
    # error payload: { "detail": { "message": "..." } }
    detail = body.get("detail", body)
    msg = detail.get("message", "") if isinstance(detail, dict) else str(detail)
    assert fragment in msg, f"訊息 '{msg}' 不含 '{fragment}'"
