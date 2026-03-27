"""Then steps for Stage 4 output verification — ReadModel Then"""

import json

from behave import then


@then('階段 4 輸出應為合法 JSON 且符合以下 Schema：')
def step_impl(context):
    stage4 = context.memo.get("stage4_result")
    assert stage4 is not None, "找不到階段 4 的輸出結果"

    # Verify it's a valid dict (JSON-serializable)
    json_str = json.dumps(stage4)
    parsed = json.loads(json_str)

    # Check required top-level fields
    assert "exam_id" in parsed, "缺少 exam_id 欄位"
    assert "total_questions" in parsed, "缺少 total_questions 欄位"
    assert "questions" in parsed, "缺少 questions 欄位"

    questions = parsed["questions"]
    assert isinstance(questions, list), "questions 應為陣列"
    assert len(questions) > 0, "questions 不應為空"

    # Check each question has required fields
    required_fields = ["id", "text", "options", "answer", "difficulty",
                       "exam_point", "explanation", "distractor_reasons"]

    for i, q in enumerate(questions):
        for field in required_fields:
            assert field in q, \
                f"第 {i+1} 題缺少 '{field}' 欄位"

        # Verify options is a list of 4
        assert isinstance(q["options"], list), f"第 {i+1} 題 options 應為陣列"
        assert len(q["options"]) == 4, \
            f"第 {i+1} 題應有 4 個選項，但得到 {len(q['options'])}"

        # Verify answer is an index 0-3
        assert isinstance(q["answer"], int), f"第 {i+1} 題 answer 應為整數"
        assert 0 <= q["answer"] <= 3, \
            f"第 {i+1} 題 answer 應在 0-3 之間，但得到 {q['answer']}"
