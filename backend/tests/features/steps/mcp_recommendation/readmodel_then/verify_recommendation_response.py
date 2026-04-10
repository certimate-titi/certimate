"""
驗證 MCP Recommendation Server 的回應
"""

from behave import then
from datetime import datetime, timedelta, timezone


@then('回應包含 {count:d} 道推薦題目')
def step_verify_question_count(context, count):
    """驗證回應包含指定數量的推薦題目"""
    response = context.last_response
    data = response.get("data", {})
    questions = data.get("questions", [])

    assert len(questions) == count, f"Expected {count} questions but got {len(questions)}"


@then('推薦題目優先來自掌握度低的知識點')
def step_verify_low_mastery_priority(context):
    """驗證推薦題目優先來自掌握度低的知識點"""
    response = context.last_response
    data = response.get("data", {})
    questions = data.get("questions", [])

    # 驗證每道題目都有理由
    for q in questions:
        reason = q.get("reason", "")
        assert "掌握度" in reason or "複習" in reason, f"Invalid reason: {reason}"


@then('每道題目包含推薦理由')
def step_verify_question_reasoning(context):
    """驗證每道題目包含推薦理由"""
    response = context.last_response
    data = response.get("data", {})
    questions = data.get("questions", [])

    for question in questions:
        assert "reason" in question, f"Missing reason in question: {question}"
        assert question["reason"], "Reason should not be empty"


@then('下次複習時間距今天數大於 {days:d} 天')
def step_verify_spacing_days(context, days):
    """驗證下次複習距今天數"""
    response = context.last_response
    data = response.get("data", {})
    days_interval = data.get("days_interval")

    assert days_interval is not None, "Missing days_interval"
    assert days_interval > days, f"Expected days_interval > {days}, got {days_interval}"


@then('下次複習時間距今 {days:d} 天')
def step_verify_exact_spacing_days(context, days):
    """驗證下次複習距今精確天數"""
    response = context.last_response
    data = response.get("data", {})
    days_interval = data.get("days_interval")

    assert days_interval is not None, "Missing days_interval"
    assert days_interval == days, f"Expected days_interval = {days}, got {days_interval}"


@then('回應包含前置知識 "{prerequisites}"')
def step_verify_prerequisites(context, prerequisites):
    """驗證回應包含指定的前置知識"""
    response = context.last_response
    data = response.get("data", {})
    prereq_list = data.get("prerequisites", [])
    prereq_names = ", ".join(f'"{p}"' for p in prereq_list)

    assert prerequisites in data.get("learning_sequence", []) or prerequisites in prereq_list, \
        f"Expected {prerequisites} in prerequisites or learning_sequence"


@then('回應包含推薦學習順序')
def step_verify_learning_sequence(context):
    """驗證回應包含推薦學習順序"""
    response = context.last_response
    data = response.get("data", {})
    sequence = data.get("learning_sequence", [])

    assert isinstance(sequence, list), "learning_sequence should be a list"
    assert len(sequence) > 0, "learning_sequence should not be empty"


@then('回應包含估計學習時間')
def step_verify_estimated_hours(context):
    """驗證回應包含估計學習時間"""
    response = context.last_response
    data = response.get("data", {})
    estimated_hours = data.get("estimated_hours")

    assert estimated_hours is not None, "Missing estimated_hours"
    assert isinstance(estimated_hours, (int, float)), "estimated_hours should be numeric"
    assert estimated_hours > 0, "estimated_hours should be > 0"


@then('節點質量驗證通過')
def step_verify_quality_passes(context):
    """驗證節點質量驗證通過"""
    response = context.last_response
    data = response.get("data", {})
    is_valid = data.get("is_valid")

    assert is_valid == True, "Node quality validation should pass"


@then('節點質量驗證失敗')
def step_verify_quality_fails(context):
    """驗證節點質量驗證失敗"""
    response = context.last_response
    data = response.get("data", {})
    is_valid = data.get("is_valid")

    assert is_valid == False, "Node quality validation should fail"


@then('質量分數大於等於 {threshold:f}')
def step_verify_quality_score(context, threshold):
    """驗證質量分數"""
    response = context.last_response
    data = response.get("data", {})
    score = data.get("score")

    assert score is not None, "Missing quality score"
    assert score >= threshold, f"Expected score >= {threshold}, got {score}"


@then('回應包含問題 "{issue}"')
def step_verify_quality_issue(context, issue):
    """驗證回應包含指定的質量問題"""
    response = context.last_response
    data = response.get("data", {})
    issues = data.get("issues", [])

    assert issue in issues, f"Expected '{issue}' in issues: {issues}"


@then('重複次數為 {repetition_count:d}')
def step_verify_repetition_count(context, repetition_count):
    """驗證重複次數"""
    response = context.last_response
    data = response.get("data", {})
    count = data.get("repetition_count")

    assert count == repetition_count, f"Expected repetition_count = {repetition_count}, got {count}"
