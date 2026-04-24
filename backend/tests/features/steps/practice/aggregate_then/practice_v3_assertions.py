"""Then 練習 V3 驗證 — Feature 07 Rule 488。"""

from behave import then

from .node_mastery_assertions import step_node_mastery_increased


@then('節點掌握度應上升（練習權重 {weight}）')
def step_node_mastery_up_weight(context, weight):
    step_node_mastery_increased(context, "V3 測試節點")


@then('API 應回傳正確答案與詳解')
def step_api_returns_answer_and_explanation(context):
    body = context.last_response.json()
    assert body.get("correct_answer"), f"缺 correct_answer：{body}"
    assert body.get("explanation"), f"缺 explanation：{body}"


@then('API 應回傳更新後的 progress 數值')
def step_api_returns_progress(context):
    body = context.last_response.json()
    progress = body.get("progress")
    assert progress, f"缺 progress：{body}"
    assert "new_progress" in progress, f"progress 缺 new_progress：{progress}"
    assert progress["new_progress"] > progress.get("old_progress", 0), \
        f"new_progress 未上升：{progress}"
