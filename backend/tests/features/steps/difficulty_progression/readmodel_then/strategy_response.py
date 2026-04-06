"""Then 出題策略回應驗證 — ReadModel Then"""

from behave import then


@then('系統應回溯到父節點 "{node_name}"（depth={depth:d}）')
def step_impl_backtrack(context, node_name, depth):
    response = context.last_response
    data = response.json()
    assert data.get("next_action") == "backtrack", \
        f"期望 next_action=backtrack, 實際={data.get('next_action')}"
    assert data.get("backtrack_to") == node_name or data.get("current_node") == node_name, \
        f"期望回溯到 '{node_name}', 實際 backtrack_to={data.get('backtrack_to')}, current_node={data.get('current_node')}"


@then('系統應回溯到根節點 "{node_name}"（depth={depth:d}）')
def step_impl_backtrack_root(context, node_name, depth):
    response = context.last_response
    data = response.json()
    assert data.get("next_action") == "backtrack", \
        f"期望 next_action=backtrack, 實際={data.get('next_action')}"
    assert data.get("current_node") == node_name, \
        f"期望回溯到 '{node_name}', 實際={data.get('current_node')}"


@then('下一題的難度應為 "{difficulty}"（父節點的難度基準）')
def step_impl_difficulty(context, difficulty):
    response = context.last_response
    data = response.json()
    assert data.get("difficulty") == difficulty, \
        f"期望 difficulty={difficulty}, 實際={data.get('difficulty')}"


@then('下一題的難度應為 "{difficulty}"')
def step_impl_difficulty_simple(context, difficulty):
    response = context.last_response
    data = response.json()
    assert data.get("difficulty") == difficulty, \
        f"期望 difficulty={difficulty}, 實際={data.get('difficulty')}"


@then('系統應維持在根節點 "{node_name}" 出題')
def step_impl_stay_root(context, node_name):
    response = context.last_response
    data = response.json()
    assert data.get("current_node") == node_name, \
        f"期望維持在 '{node_name}', 實際={data.get('current_node')}"
    assert data.get("next_action") == "stay", \
        f"期望 next_action=stay, 實際={data.get('next_action')}"


@then('下一題的難度應維持 "{difficulty}"')
def step_impl_stay_difficulty(context, difficulty):
    response = context.last_response
    data = response.json()
    assert data.get("difficulty") == difficulty, \
        f"期望 difficulty={difficulty}, 實際={data.get('difficulty')}"


@then('回應應包含 hint: "{hint}"')
def step_impl_hint(context, hint):
    response = context.last_response
    data = response.json()
    assert "hint" in data, f"回應缺少 hint 欄位"
    assert hint in data["hint"], \
        f"期望 hint 包含 '{hint}', 實際='{data['hint']}'"


@then('系統不應觸發回溯（未達連續 {count:d} 題門檻）')
def step_impl_no_backtrack(context, count):
    response = context.last_response
    data = response.json()
    assert data.get("next_action") in ("stay", None), \
        f"不應觸發回溯, 實際 next_action={data.get('next_action')}"


@then('下一題仍在節點 "{node_name}" 出題')
def step_impl_stay_node(context, node_name):
    response = context.last_response
    data = response.json()
    assert data.get("current_node") == node_name, \
        f"期望仍在 '{node_name}', 實際={data.get('current_node')}"


@then('系統應觸發回溯到父節點 "{node_name}"')
def step_impl_trigger_backtrack(context, node_name):
    response = context.last_response
    data = response.json()
    assert data.get("next_action") == "backtrack", \
        f"期望 backtrack, 實際={data.get('next_action')}"
    assert data.get("current_node") == node_name, \
        f"期望回溯到 '{node_name}', 實際={data.get('current_node')}"


@then('系統應遞進回 "{node_name}"（depth={depth:d}）')
def step_impl_progress(context, node_name, depth):
    response = context.last_response
    data = response.json()
    assert data.get("next_action") == "progress", \
        f"期望 next_action=progress, 實際={data.get('next_action')}"
    assert data.get("current_node") == node_name, \
        f"期望遞進回 '{node_name}', 實際={data.get('current_node')}"


@then('系統應再次回溯到 "{node_name}"')
def step_impl_re_backtrack(context, node_name):
    response = context.last_response
    data = response.json()
    assert data.get("next_action") == "backtrack", \
        f"期望 next_action=backtrack, 實際={data.get('next_action')}"
    assert data.get("current_node") == node_name, \
        f"期望回溯到 '{node_name}', 實際={data.get('current_node')}"


@then('系統不應觸發遞進（未達連續 {count:d} 題門檻）')
def step_impl_no_progress(context, count):
    response = context.last_response
    data = response.json()
    assert data.get("next_action") in ("stay", None), \
        f"不應觸發遞進, 實際 next_action={data.get('next_action')}"


@then('下一題仍在 "{node_name}" 出題')
def step_impl_stay(context, node_name):
    response = context.last_response
    data = response.json()
    assert data.get("current_node") == node_name, \
        f"期望仍在 '{node_name}', 實際={data.get('current_node')}"
