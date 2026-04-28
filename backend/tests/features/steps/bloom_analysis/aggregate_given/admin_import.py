"""管理員匯入考古題 — Given 步驟（B-route：admin import endpoint 不存在，使用 memo 模擬）。"""

from behave import given


@given('管理員已上傳格式正確的考古題 JSON（{count:d} 題，bloom_category 為 null）')
def step_admin_uploaded_questions(context, count):
    questions = []
    for i in range(1, count + 1):
        questions.append({
            "question_number": i,
            "content": f"考古題 {i}",
            "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
            "correct_answer": "A",
            "bloom_category": None,
        })
    context.memo["admin_uploaded_questions"] = questions


@given('管理員上傳的考古題 JSON 缺少 correct_answer 欄位')
def step_admin_uploaded_invalid(context):
    questions = []
    for i in range(1, 6):
        q = {
            "question_number": i,
            "content": f"題 {i}",
            "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
            "correct_answer": "A",
        }
        if i == 3:  # 第 3 題缺 correct_answer
            q.pop("correct_answer")
        questions.append(q)
    context.memo["admin_uploaded_invalid_questions"] = questions
