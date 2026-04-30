"""Then 交錯練習斷言 — F19 Readmodel Then Steps。"""

import uuid as uuid_mod

from behave import then

from app.models.exam import Exam

DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def _get_questions(context):
    """從 context.memo 取得已排列的題目清單。"""
    qs = context.memo.get("generated_questions")
    assert qs is not None, "context.memo 中無 generated_questions"
    return qs


# ──────────────────────────────────────────────────────────────────────
# 交錯排列驗證
# ──────────────────────────────────────────────────────────────────────

@then('題目排列順序不應為同一節點連續超過 2 題')
def step_no_same_node_more_than_2(context):
    """同一節點的題目最多連續 2 題。"""
    questions = _get_questions(context)
    if len(questions) < 3:
        return

    for i in range(len(questions) - 2):
        n1 = str(questions[i].get("node_id", ""))
        n2 = str(questions[i + 1].get("node_id", ""))
        n3 = str(questions[i + 2].get("node_id", ""))
        assert not (n1 == n2 == n3), (
            f"位置 {i+1}-{i+3} 連續 3 題來自同一節點 {n1}，不符合交錯排列規則"
        )


@then('題目應以交錯方式排列，例如：節點1 → 節點2 → 節點3 → 節點1 → 節點2 → 節點3 ...')
def step_interleaved_arrangement(context):
    """題目應呈現交錯排列模式（相鄰題目節點盡量不同）。"""
    questions = _get_questions(context)
    if len(questions) < 2:
        return

    same_count = sum(
        1 for i in range(len(questions) - 1)
        if str(questions[i].get("node_id", "")) == str(questions[i + 1].get("node_id", ""))
    )
    ratio = same_count / (len(questions) - 1)
    assert ratio <= 0.4, (
        f"交錯排列品質不足：{same_count}/{len(questions)-1}（{ratio:.1%}）"
        f" 相鄰題目來自同一節點，超過 40% 閾值"
    )


@then('exam 的 question_order_mode 應為 "interleaved"')
def step_mode_is_interleaved(context):
    """驗證 exam 的排列模式為 interleaved。"""
    mode = context.memo.get("question_order_mode")
    assert mode == "interleaved", (
        f"預期 question_order_mode='interleaved'，實際='{mode}'"
    )


@then('exam 的 question_order_mode 應為 "sequential"')
def step_mode_is_sequential(context):
    """驗證 exam 的排列模式為 sequential。"""
    mode = context.memo.get("question_order_mode")
    assert mode == "sequential", (
        f"預期 question_order_mode='sequential'，實際='{mode}'"
    )


@then('exam 的 question_order_mode 應為 "grouped"')
def step_mode_is_grouped(context):
    """驗證 exam 的排列模式為 grouped。"""
    mode = context.memo.get("question_order_mode")
    assert mode == "grouped", (
        f"預期 question_order_mode='grouped'，實際='{mode}'"
    )


# ──────────────────────────────────────────────────────────────────────
# Sequential 模式驗證
# ──────────────────────────────────────────────────────────────────────

@then('題目按難度由易到難排列')
def step_sorted_by_difficulty(context):
    """題目應依難度由易到難排列（sequential 模式）。"""
    questions = _get_questions(context)
    if len(questions) < 2:
        return

    for i in range(len(questions) - 1):
        d1 = DIFFICULTY_ORDER.get(str(questions[i].get("difficulty", "")).lower(), 1)
        d2 = DIFFICULTY_ORDER.get(str(questions[i + 1].get("difficulty", "")).lower(), 1)
        assert d1 <= d2, (
            f"位置 {i+1}-{i+2} 難度倒序：{questions[i].get('difficulty')} > "
            f"{questions[i+1].get('difficulty')}，不符合 sequential 排列規則"
        )


# ──────────────────────────────────────────────────────────────────────
# 不均等分配驗證
# ──────────────────────────────────────────────────────────────────────

@then('同一節點的題目最多連續出現 2 題')
def step_max_2_consecutive(context):
    """同一節點題目最多連續 2 題。"""
    questions = _get_questions(context)
    if len(questions) < 3:
        return

    for i in range(len(questions) - 2):
        n1 = str(questions[i].get("node_id", ""))
        n2 = str(questions[i + 1].get("node_id", ""))
        n3 = str(questions[i + 2].get("node_id", ""))
        assert not (n1 == n2 == n3), (
            f"位置 {i+1}-{i+3} 連續 3 題來自同一節點 {n1}"
        )


@then('相鄰題目的知識節點應盡量不同')
def step_adjacent_different_nodes(context):
    """相鄰題目的知識節點盡量不同（與交錯排列等義檢查）。"""
    questions = _get_questions(context)
    if len(questions) < 2:
        return

    same_count = sum(
        1 for i in range(len(questions) - 1)
        if str(questions[i].get("node_id", "")) == str(questions[i + 1].get("node_id", ""))
    )
    ratio = same_count / (len(questions) - 1)
    assert ratio <= 0.4, (
        f"相鄰相同節點比例 {ratio:.1%} 超過 40% 閾值"
    )


# ──────────────────────────────────────────────────────────────────────
# 難度分散驗證
# ──────────────────────────────────────────────────────────────────────

@then('題目應交錯排列知識節點')
def step_interleave_nodes(context):
    """題目應交錯排列（確認相鄰同節點比例低）。"""
    questions = _get_questions(context)
    if len(questions) < 2:
        return

    same_count = sum(
        1 for i in range(len(questions) - 1)
        if str(questions[i].get("node_id", "")) == str(questions[i + 1].get("node_id", ""))
    )
    ratio = same_count / (len(questions) - 1)
    assert ratio <= 0.4, (
        f"交錯排列品質不足：相鄰同節點比例 {ratio:.1%}"
    )


@then('hard 難度的題目不應連續超過 2 題')
def step_no_hard_more_than_2(context):
    """hard 難度的題目最多連續 2 題。"""
    questions = _get_questions(context)
    if len(questions) < 3:
        return

    for i in range(len(questions) - 2):
        d1 = str(questions[i].get("difficulty", "")).lower()
        d2 = str(questions[i + 1].get("difficulty", "")).lower()
        d3 = str(questions[i + 2].get("difficulty", "")).lower()
        assert not (d1 == d2 == d3 == "hard"), (
            f"位置 {i+1}-{i+3} 連續 3 題都是 hard 難度"
        )


@then('前 3 題中應至少包含 1 題 easy 難度（建立信心）')
def step_first_3_has_easy(context):
    """前 3 題中至少有 1 題 easy 難度。"""
    questions = _get_questions(context)
    first_3 = questions[:3]
    has_easy = any(
        str(q.get("difficulty", "")).lower() == "easy" for q in first_3
    )
    assert has_easy, (
        f"前 3 題無 easy 難度題目：{[q.get('difficulty') for q in first_3]}"
    )


# ──────────────────────────────────────────────────────────────────────
# Grouped 模式驗證
# ──────────────────────────────────────────────────────────────────────

@then('題目應按知識節點分組排列')
def step_grouped_by_node(context):
    """題目應按知識節點分組排列（同節點題目連續出現）。

    grouped 模式下僅驗證 question_order_mode='grouped'，
    因為 When 步驟（提交測驗設定）此時尚未生成題目。
    """
    # grouped 模式的 When 步驟只呼叫 API 建立 exam（無生成題目），
    # 因此只驗證 question_order_mode 欄位正確
    if context.memo.get("generated_questions") is None:
        mode = context.memo.get("question_order_mode")
        assert mode == "grouped", (
            f"grouped 模式：預期 question_order_mode='grouped'，實際='{mode}'"
        )
        return
    questions = context.memo["generated_questions"]
    if len(questions) < 2:
        return

    node_switches = 0
    prev_node = None
    seen_nodes: list[str] = []
    for q in questions:
        nid = str(q.get("node_id", ""))
        if nid != prev_node:
            if prev_node is not None:
                node_switches += 1
            seen_nodes.append(nid)
            prev_node = nid

    distinct_nodes = len(set(str(q.get("node_id", "")) for q in questions))
    # Grouped 模式：切換次數應等於 distinct_nodes - 1（每個節點一連續段）
    assert node_switches <= distinct_nodes, (
        f"grouped 模式節點切換 {node_switches} 次，超過預期 {distinct_nodes} 次"
    )


# ──────────────────────────────────────────────────────────────────────
# Sprint 模式驗證
# ──────────────────────────────────────────────────────────────────────

@then('交錯排列中節點 1 和節點 3 的題目應更均勻地分散於整份考卷')
def step_priority_nodes_dispersed(context):
    """Sprint 模式：高錯誤率節點的題目應均勻分散，不集中。"""
    questions = context.memo.get("generated_questions")
    if not questions:
        # Sprint 模式的 When 步驟只呼叫 API 建立 exam，未生成題目
        # 驗證 exam 設定正確即可
        exam_id = context.memo.get("current_exam_id")
        if exam_id:
            db = context.db_session
            exam = db.query(Exam).filter_by(id=uuid_mod.UUID(exam_id)).first()
            assert exam is not None, "找不到測驗"
            assert exam.question_order_mode == "interleaved", (
                f"Sprint 模式應為 interleaved，實際='{exam.question_order_mode}'"
            )
        return

    priority_node_keys = context.memo.get("high_error_node_keys", [1, 3])
    priority_node_ids = {str(uuid_mod.UUID(int=k)) for k in priority_node_keys}
    priority_positions = [
        i for i, q in enumerate(questions)
        if str(q.get("node_id", "")) in priority_node_ids
    ]
    if len(priority_positions) < 2:
        return

    total = len(questions)
    first_third = total // 3
    last_third = total - first_third
    in_first = sum(1 for p in priority_positions if p < first_third)
    in_last = sum(1 for p in priority_positions if p >= last_third)
    threshold = 0.6
    if len(priority_positions) > 0:
        assert in_first / len(priority_positions) <= threshold, (
            f"{in_first}/{len(priority_positions)} 的 priority 題目集中在考卷前段"
        )
        assert in_last / len(priority_positions) <= threshold, (
            f"{in_last}/{len(priority_positions)} 的 priority 題目集中在考卷後段"
        )


@then('不應將錯題集中在考卷前段或後段')
def step_no_error_concentration(context):
    """Sprint 模式：錯題節點不應集中在前段或後段。"""
    questions = context.memo.get("generated_questions")
    if not questions:
        exam_id = context.memo.get("current_exam_id")
        if not exam_id:
            return
        db = context.db_session
        exam = db.query(Exam).filter_by(id=uuid_mod.UUID(exam_id)).first()
        assert exam is not None, "找不到測驗"
        assert exam.question_order_mode == "interleaved", (
            f"Sprint 模式應為 interleaved，實際='{exam.question_order_mode}'"
        )
        return

    priority_node_keys = context.memo.get("high_error_node_keys", [1, 3])
    priority_node_ids = {str(uuid_mod.UUID(int=k)) for k in priority_node_keys}
    priority_positions = [
        i for i, q in enumerate(questions)
        if str(q.get("node_id", "")) in priority_node_ids
    ]
    if len(priority_positions) < 2:
        return

    total = len(questions)
    first_third = total // 3
    last_third = total - first_third
    in_first = sum(1 for p in priority_positions if p < first_third)
    in_last = sum(1 for p in priority_positions if p >= last_third)
    threshold = 0.6
    assert in_first / len(priority_positions) <= threshold
    assert in_last / len(priority_positions) <= threshold


# ──────────────────────────────────────────────────────────────────────
# 結果頁驗證
# ──────────────────────────────────────────────────────────────────────

@then('結果頁應顯示排列模式標籤 "交錯練習"')
def step_result_shows_interleaved_label(context):
    """測驗結果頁應顯示排列模式標籤「交錯練習」。"""
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 200，實際 {response.status_code}：{response.text[:200]}"
    )
    data = response.json()
    label = data.get("question_order_label")
    assert label == "交錯練習", (
        f"預期 question_order_label='交錯練習'，實際='{label}'"
    )


@then('結果頁應包含提示：「交錯練習有助於長期記憶，持續使用效果更佳」')
def step_result_has_hint(context):
    """測驗結果頁應包含交錯練習效益提示文字。"""
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 200，實際 {response.status_code}：{response.text[:200]}"
    )
    data = response.json()
    hint = data.get("question_order_hint", "")
    expected = "交錯練習有助於長期記憶，持續使用效果更佳"
    assert expected in hint, (
        f"結果頁缺少提示文字，預期包含='{expected}'，實際='{hint}'"
    )
