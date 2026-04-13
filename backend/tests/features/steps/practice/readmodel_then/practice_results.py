"""Then 練習作答結果驗證。"""

from behave import then


@then('回應應包含 {count:d} 道練習題')
def step_question_count(context, count):
    data = context.last_response.json()
    questions = data.get("questions", [])
    assert len(questions) == count, \
        f"預期 {count} 道練習題，實際 {len(questions)} 道"


@then('作答結果為正確')
def step_is_correct(context):
    data = context.last_response.json()
    assert data.get("is_correct") is True, \
        f"預期作答正確，實際 is_correct={data.get('is_correct')}"


@then('作答結果為錯誤')
def step_is_incorrect(context):
    data = context.last_response.json()
    assert data.get("is_correct") is False, \
        f"預期作答錯誤，實際 is_correct={data.get('is_correct')}"


@then('回應應包含正確答案 "{answer}"')
def step_correct_answer(context, answer):
    data = context.last_response.json()
    assert data.get("correct_answer") == answer, \
        f"預期正確答案 '{answer}'，實際 '{data.get('correct_answer')}'"


@then('回應應包含詳解')
def step_has_explanation(context):
    data = context.last_response.json()
    explanation = data.get("explanation", "")
    assert explanation and explanation != "尚無詳解", \
        f"預期有詳解，實際 '{explanation}'"


@then('節點 "{node_name}" 的進度應已更新')
def step_node_progress_updated(context, node_name):
    data = context.last_response.json()
    progress = data.get("progress")
    assert progress is not None, "回應中應包含 progress 欄位"
    assert data.get("state_updated") is True, "state_updated 應為 True"


@then('父節點 "{node_name}" 的進度應已傳播更新')
def step_parent_propagated(context, node_name):
    data = context.last_response.json()
    propagation = data.get("propagation", [])
    assert len(propagation) > 0, \
        f"預期有傳播更新，實際 propagation 為空"
