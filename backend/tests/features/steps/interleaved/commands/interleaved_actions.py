"""When 交錯練習操作 — F19 Command Steps。"""

import uuid as uuid_mod

from behave import when

from app.models.exam import Exam, ExamStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.resource import Resource
from app.services.interleaved_practice_service import apply_order_mode


def _get_exam(context):
    """從 context.memo 取得目前測驗。"""
    exam_id = context.memo.get("current_exam_id")
    assert exam_id, "context.memo 中無 current_exam_id"
    db = context.db_session
    exam = db.query(Exam).filter_by(id=uuid_mod.UUID(exam_id)).first()
    assert exam, f"找不到測驗 {exam_id}"
    return exam


def _ensure_historical_exam(context):
    """確保有一個 HistoricalExam（滿足 CHECK 約束）。"""
    if context.memo.get("practice_exam_id"):
        return uuid_mod.UUID(context.memo["practice_exam_id"])
    db = context.db_session
    from app.models.historical_exam import HistoricalExam
    he = HistoricalExam(
        exam_code="INTERLEAVED",
        exam_name="交錯練習題庫",
        category_code="interleaved",
        subject_code="interleaved_general",
    )
    db.add(he)
    db.flush()
    context.memo["practice_exam_id"] = str(he.id)
    return he.id


def _create_questions_for_node(db, exam_id, node_id, node_key, count, start_num,
                                difficulties, historical_exam_id):
    """為指定節點建立若干題目。"""
    questions = []
    for i in range(count):
        diff = difficulties[i % len(difficulties)]
        q = Question(
            exam_id=exam_id,
            node_id=node_id,
            historical_exam_id=historical_exam_id,
            question_number=start_num + i,
            type="single_choice",
            difficulty=diff,
            content=f"節點{node_key}第{i+1}題",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
            explanation="詳解",
        )
        db.add(q)
        questions.append(q)
    return questions


@when('AI 生成 9 題完成，各節點各 3 題')
def step_ai_generate_9_equal(context):
    """模擬 AI 生成 9 題完成，各節點各 3 題，並執行交錯排列。"""
    exam = _get_exam(context)
    db = context.db_session
    historical_exam_id = _ensure_historical_exam(context)

    difficulties = ["easy", "medium", "hard"]
    node_keys = [1, 2, 3]
    all_questions = []
    q_num = 1

    db.flush()

    for nk in node_keys:
        node_id = uuid_mod.UUID(int=nk)
        qs = _create_questions_for_node(
            db, exam.id, node_id, nk, 3, q_num, difficulties, historical_exam_id
        )
        q_num += 3
        all_questions.extend(qs)

    db.flush()

    # 執行交錯排列
    q_dicts = [
        {"node_id": str(q.node_id), "difficulty": q.difficulty, "id": str(q.id)}
        for q in all_questions
    ]
    ordered = apply_order_mode(q_dicts, exam.question_order_mode or "interleaved")

    # 更新 question_number：先設為負數（臨時值）避免唯一約束衝突，再設最終值
    q_map = {str(q.id): q for q in all_questions}
    for i, q in enumerate(all_questions):
        q.question_number = -(i + 1)
    db.flush()
    for item in ordered:
        q = q_map.get(item["id"])
        if q:
            q.question_number = item["question_number"]

    exam.status = ExamStatus.READY
    db.commit()

    context.memo["generated_questions"] = ordered


@when('AI 生成 10 題完成')
def step_ai_generate_10(context):
    """模擬 AI 生成 10 題完成。

    根據 exam 的 difficulty_distribution 分配難度，
    若有多個節點則均等分配（每節點各 5 題），
    若只有 1 個節點則全部屬於節點 1。
    """
    exam = _get_exam(context)
    db = context.db_session
    historical_exam_id = _ensure_historical_exam(context)

    total = 10
    mode = exam.question_order_mode or "sequential"

    # 從 exam.difficulty_distribution 取難度分配
    diff_dist = exam.difficulty_distribution or {}
    easy_pct = diff_dist.get("easy", 30)
    medium_pct = diff_dist.get("medium", 50)
    hard_pct = diff_dist.get("hard", 20)

    easy_count = max(1, round(total * easy_pct / 100))
    hard_count = max(1, round(total * hard_pct / 100))
    medium_count = total - easy_count - hard_count

    # 建立難度序列（easy 先，medium 次，hard 後）
    diff_seq = (["easy"] * easy_count + ["medium"] * medium_count + ["hard"] * hard_count)[:total]

    # 根據 exam 的 node_ids（stored in difficulty_distribution["node_ids"]）決定節點
    node_keys_from_dist = diff_dist.get("node_ids", [])
    if node_keys_from_dist:
        # 多節點：從 context.ids 查已建立的節點
        available_node_ids = []
        for nid_str in node_keys_from_dist:
            # nid_str 是 UUID 格式
            available_node_ids.append(nid_str)
    else:
        available_node_ids = [str(uuid_mod.UUID(int=1))]

    all_questions = []
    for i, diff in enumerate(diff_seq, start=1):
        nid_str = available_node_ids[i % len(available_node_ids)]
        q = Question(
            exam_id=exam.id,
            node_id=uuid_mod.UUID(nid_str),
            historical_exam_id=historical_exam_id,
            question_number=i,
            type="single_choice",
            difficulty=diff,
            content=f"題目{i}（{diff}）",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
            explanation="詳解",
        )
        db.add(q)
        all_questions.append(q)

    db.flush()

    q_dicts = [
        {"node_id": str(q.node_id), "difficulty": q.difficulty, "id": str(q.id)}
        for q in all_questions
    ]
    ordered = apply_order_mode(q_dicts, mode)

    # 先設負數臨時值，避免唯一約束衝突
    q_map = {str(q.id): q for q in all_questions}
    for i, q in enumerate(all_questions):
        q.question_number = -(i + 1)
    db.flush()
    for item in ordered:
        q = q_map.get(item["id"])
        if q:
            q.question_number = item["question_number"]

    exam.status = ExamStatus.READY
    db.commit()

    context.memo["generated_questions"] = ordered


@when('AI 生成 10 題完成，節點 1 有 4 題、節點 2 有 3 題、節點 3 有 3 題')
def step_ai_generate_10_uneven(context):
    """模擬 AI 生成 10 題完成（不均等分配），並執行交錯排列。"""
    exam = _get_exam(context)
    db = context.db_session
    historical_exam_id = _ensure_historical_exam(context)

    node_distribution = [(1, 4), (2, 3), (3, 3)]
    all_questions = []
    q_num = 1

    for nk, count in node_distribution:
        node_id = uuid_mod.UUID(int=nk)
        difficulties = ["easy", "medium", "hard", "medium"]
        qs = _create_questions_for_node(
            db, exam.id, node_id, nk, count, q_num, difficulties, historical_exam_id
        )
        q_num += count
        all_questions.extend(qs)

    db.flush()

    q_dicts = [
        {"node_id": str(q.node_id), "difficulty": q.difficulty, "id": str(q.id)}
        for q in all_questions
    ]
    ordered = apply_order_mode(q_dicts, exam.question_order_mode or "interleaved")

    # 先設負數臨時值，避免唯一約束衝突
    q_map = {str(q.id): q for q in all_questions}
    for i, q in enumerate(all_questions):
        q.question_number = -(i + 1)
    db.flush()
    for item in ordered:
        q = q_map.get(item["id"])
        if q:
            q.question_number = item["question_number"]

    exam.status = ExamStatus.READY
    db.commit()

    context.memo["generated_questions"] = ordered


@when('使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2、3，題數為 9，排列模式為 "集中練習"')
def step_submit_grouped_mode(context):
    """提交集中練習模式測驗設定。"""
    email = "pro@example.com"
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    token = context.jwt_helper.generate_token(user_id)
    node_uuids = [str(uuid_mod.UUID(int=k)) for k in [1, 2, 3]]

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": node_uuids,
            "question_count": 9,
            "question_order_mode": "集中練習",
        },
    )
    context.last_response = response
    data = response.json()
    context.memo["current_exam_id"] = data.get("exam_id")
    context.memo["question_order_mode"] = data.get("question_order_mode")


@when('使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2、3，題數為 9，排列模式為 "交錯練習"')
def step_submit_interleaved_mode(context):
    """提交交錯練習模式測驗設定。"""
    email = "pro@example.com"
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    token = context.jwt_helper.generate_token(user_id)
    node_uuids = [str(uuid_mod.UUID(int=k)) for k in [1, 2, 3]]

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": node_uuids,
            "question_count": 9,
            "question_order_mode": "交錯練習",
        },
    )
    context.last_response = response
    data = response.json()
    context.memo["current_exam_id"] = data.get("exam_id")
    context.memo["question_order_mode"] = data.get("question_order_mode")


@when('使用者提交測驗設定，選擇節點 1、2、3、4，題數為 20')
def step_submit_sprint_4nodes_20(context):
    """Sprint 模式：提交 4 節點測驗設定（20 題）。"""
    email = "pro@example.com"
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    token = context.jwt_helper.generate_token(user_id)
    node_uuids = [str(uuid_mod.UUID(int=k)) for k in [1, 2, 3, 4]]

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": node_uuids,
            "question_count": 20,
            "question_order_mode": "interleaved",
        },
    )
    context.last_response = response
    data = response.json()
    context.memo["current_exam_id"] = data.get("exam_id")
    context.memo["question_order_mode"] = data.get("question_order_mode")


# 注意：'使用者查看測驗結果' step 定義於 pomodoro/commands/pomodoro_actions.py
# 並已更新為支援 context.memo["current_exam_id"] + /result endpoint
