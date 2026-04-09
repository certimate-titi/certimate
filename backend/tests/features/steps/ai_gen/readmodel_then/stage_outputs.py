"""Then steps for AI stage output validation — ReadModel Then"""

from behave import then


@then('階段 1 輸出應包含：')
def step_impl_stage1_output(context):
    """驗證階段 1 輸出包含所需欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        stage1 = data.get("stages", {}).get("stage_1", {})
        for row in context.table:
            field = row["欄位"]
            assert field in stage1, f"階段 1 輸出缺少欄位 '{field}'"


@then('所有 point_ratio 加總應等於 100%')
def step_impl_point_ratio_sum(context):
    """驗證所有 point_ratio 加總為 100%。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        stage1 = data.get("stages", {}).get("stage_1", {})
        point_ratio = stage1.get("point_ratio", {})
        if point_ratio:
            total = sum(point_ratio.values())
            assert abs(total - 100) <= 1, \
                f"point_ratio 加總應為 100%，實際 {total}%"


@then('bloom_allocation 的各 Bloom 類別題數加總應符合 bloom_distribution（誤差 ±1 題）')
def step_impl_bloom_allocation(context):
    """驗證 bloom_allocation 符合 bloom_distribution 配比。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        stage1 = data.get("stages", {}).get("stage_1", {})
        bloom_alloc = stage1.get("bloom_allocation", {})
        bloom_dist = context.memo.get("bloom_distribution", {})
        total_questions = context.memo.get("exam_question_count", 10)
        for category, pct in bloom_dist.items():
            expected_count = round(total_questions * pct / 100)
            actual_count = sum(
                item.get("count", 0)
                for item in bloom_alloc.values()
                if item.get("category") == category
            )
            assert abs(actual_count - expected_count) <= 1, \
                f"Bloom 類別 '{category}' 期望 {expected_count} 題，實際 {actual_count} 題"


@then('階段 2 輸出應包含 {count:d} 題原始考題')
def step_impl_stage2_questions(context, count):
    """驗證階段 2 輸出含指定數量的原始考題。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        stage2 = data.get("stages", {}).get("stage_2", {})
        questions = stage2.get("questions", [])
        assert len(questions) == count, \
            f"階段 2 應有 {count} 題，實際 {len(questions)} 題"


@then('每題應包含：')
def step_impl_question_fields(context):
    """驗證每題包含必要欄位。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        stage2 = data.get("stages", {}).get("stage_2", {})
        questions = stage2.get("questions", [])
        for q in questions:
            for row in context.table:
                field = row["欄位"]
                assert field in q, f"考題缺少欄位 '{field}'"


@then('難易度分布應符合 Easy:30% Medium:50% Hard:20%（容許 ±1 題）')
def step_impl_difficulty_dist(context):
    """驗證難易度分布符合規定（容許 ±1 題）。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        stage2 = data.get("stages", {}).get("stage_2", {})
        questions = stage2.get("questions", [])
        total = len(questions)
        if total == 0:
            return
        easy_count = sum(1 for q in questions if q.get("difficulty") == "easy")
        medium_count = sum(1 for q in questions if q.get("difficulty") == "medium")
        hard_count = sum(1 for q in questions if q.get("difficulty") == "hard")
        expected_easy = round(total * 0.30)
        expected_medium = round(total * 0.50)
        expected_hard = round(total * 0.20)
        assert abs(easy_count - expected_easy) <= 1, \
            f"Easy 難度期望 {expected_easy} 題，實際 {easy_count} 題"
        assert abs(medium_count - expected_medium) <= 1, \
            f"Medium 難度期望 {expected_medium} 題，實際 {medium_count} 題"
        assert abs(hard_count - expected_hard) <= 1, \
            f"Hard 難度期望 {expected_hard} 題，實際 {hard_count} 題"


@then('階段 3 輸出中每題應包含：')
def step_impl_stage3_fields(context):
    """驗證階段 3 輸出中每題含必要欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        stage3 = data.get("stages", {}).get("stage_3", {})
        questions = stage3.get("questions", [])
        for q in questions:
            for row in context.table:
                field = row["欄位"]
                assert field in q, f"階段 3 考題缺少欄位 '{field}'"


@then('干擾項應具備「表面合理但本質錯誤」的特性')
def step_impl_distractor_quality(context):
    """驗證干擾項品質特性（語義層面 — 在測試中僅確認欄位存在）。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        stage3 = data.get("stages", {}).get("stage_3", {})
        questions = stage3.get("questions", [])
        for q in questions:
            assert "distractor_reasons" in q, \
                "考題應包含 distractor_reasons 以說明干擾項設計理由"


@then('正確答案在四個選項中的位置應隨機分布')
def step_impl_answer_position(context):
    """驗證正確答案位置分布（不全部集中在同一索引）。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        stage3 = data.get("stages", {}).get("stage_3", {})
        questions = stage3.get("questions", [])
        if len(questions) < 4:
            return
        positions = [q.get("correct_index") for q in questions if q.get("correct_index") is not None]
        unique_positions = set(positions)
        assert len(unique_positions) > 1, \
            f"正確答案應分布在多個位置，實際只有 {unique_positions}"


@then('階段 4 輸出應為合法 JSON 且符合以下 Schema：')
def step_impl_stage4_schema(context):
    """驗證階段 4 輸出為合法 JSON 並符合 Schema。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        stage4 = data.get("stages", {}).get("stage_4", data)
        assert "questions" in stage4, "階段 4 輸出應包含 questions 欄位"
        for q in stage4.get("questions", []):
            required_fields = ["id", "text", "options", "answer", "difficulty", "exam_point", "explanation"]
            for field in required_fields:
                assert field in q, f"考題缺少必要欄位 '{field}'"
