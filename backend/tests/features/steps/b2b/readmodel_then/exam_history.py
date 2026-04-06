"""Then steps — 考試歷程與錯題回應驗證."""
from behave import then


@then('回應中 exam_history 應包含 {count:d} 筆考試紀錄')
def step_exam_history_count(context, count):
    """Verify exam_history count in response."""

    resp = context.last_response.json()
    history = resp.get("exam_history", [])
    assert len(history) == count, f"Expected {count} exam records, got {len(history)}"


@then('該考試紀錄的 wrong_answers 應包含 {count:d} 筆錯題')
def step_wrong_answers_count(context, count):
    """Verify wrong_answers count in the first exam record."""

    resp = context.last_response.json()
    history = resp.get("exam_history", [])
    assert len(history) > 0, "No exam history found"
    wrong = history[0].get("wrong_answers", [])
    assert len(wrong) == count, f"Expected {count} wrong answers, got {len(wrong)}"


@then('每筆錯題應包含：')
def step_wrong_answer_fields(context):
    """Verify each wrong answer has required fields."""

    resp = context.last_response.json()
    history = resp.get("exam_history", [])
    assert len(history) > 0
    wrong = history[0].get("wrong_answers", [])
    required_fields = [row["欄位"] for row in context.table]
    for wa in wrong:
        for field in required_fields:
            assert field in wa, f"Missing field '{field}' in wrong answer: {wa.keys()}"


@then('回應中 exam_count 應為 {count:d}')
def step_exam_count(context, count):
    """Verify exam_count in response."""

    resp = context.last_response.json()
    assert resp.get("exam_count") == count, \
        f"Expected exam_count={count}, got {resp.get('exam_count')}"


@then('回應中 exam_history 應為空陣列')
def step_exam_history_empty(context):
    """Verify exam_history is empty array."""

    resp = context.last_response.json()
    history = resp.get("exam_history", [])
    assert len(history) == 0, f"Expected empty exam_history, got {len(history)} records"
