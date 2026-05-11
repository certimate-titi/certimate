"""Then assertions — Feature 45 depth CHECK BDD."""

from behave import then


@then('KnowledgeNode 寫入成功')
def step_assert_node_persisted(context):
    err = context.memo.get("last_node_error")
    assert not err, f"預期寫入成功，實際 error: {err}"
    node = context.memo.get("last_created_node")
    assert node is not None, "預期建立的節點存在於 memo"


@then('該節點 depth 為 {n:d}')
def step_assert_node_depth(context, n):
    node = context.memo.get("last_created_node")
    assert node is not None, "需先有 last_created_node"
    assert node.depth == n, f"預期 depth={n}，實際 depth={node.depth}"


@then('該 root 節點 depth 為 {n:d}')
def step_assert_root_depth(context, n):
    step_assert_node_depth(context, n)


@then('該節點 depth 為 {n:d} 不違反 CHECK')
def step_assert_node_depth_check_ok(context, n):
    step_assert_node_depth(context, n)


@then('新節點 depth 為 {n:d}')
def step_assert_new_node_depth(context, n):
    step_assert_node_depth(context, n)


@then('寫入 DB 不觸發 chk_depth_range CHECK 違規')
def step_assert_no_check_violation(context):
    err = context.memo.get("last_node_error") or ""
    assert "chk_depth_range" not in err, (
        f"預期無 chk_depth_range 違規，實際 error: {err}"
    )
    assert "violates check constraint" not in err.lower(), (
        f"預期無 CHECK 違規，實際 error: {err}"
    )
