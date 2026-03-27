"""Given steps for individual AI generation stages — Aggregate Given"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus
from app.services.ai_generation_service import AiGenerationService


@given('階段 1 已輸出含 {num_points:d} 個考點、各 {per_point:d} 題的考綱')
def step_impl(context, num_points, per_point):
    # Simulate stage 1 output
    exam_points = []
    total_q = num_points * per_point
    base_ratio = 100 // num_points
    remainder = 100 - base_ratio * num_points

    for i in range(num_points):
        ratio = base_ratio + (1 if i < remainder else 0)
        exam_points.append({
            "name": f"考點_{i+1}",
            "node_id": str(uuid.uuid4()),
            "ratio": ratio,
            "suggested_difficulty": {"easy": 30, "medium": 50, "hard": 20},
        })

    context.memo["stage1_result"] = {
        "exam_points": exam_points,
        "point_ratio": {p["name"]: p["ratio"] for p in exam_points},
        "difficulty_map": {p["name"]: p["suggested_difficulty"] for p in exam_points},
    }
    context.memo["total_questions"] = total_q
    context.memo["difficulty_distribution"] = {"easy": 30, "medium": 50, "hard": 20}


@given('階段 2 已輸出 {num_q:d} 題原始考題')
def step_impl(context, num_q):
    questions = []
    for i in range(num_q):
        diff = "easy" if i < 3 else ("medium" if i < 8 else "hard")
        questions.append({
            "question_text": f"考題_{i+1}",
            "correct_answer": f"正確答案_{i+1}",
            "difficulty": diff,
            "exam_point": f"考點_{(i % 5) + 1}",
        })

    context.memo["stage2_result"] = {
        "questions": questions,
        "total": num_q,
    }


@given('階段 3 已輸出 {num_q:d} 題完整考題')
def step_impl(context, num_q):
    import random
    questions = []
    for i in range(num_q):
        correct = f"正確答案_{i+1}"
        distractors = [f"干擾項_{chr(65+j)}_{i+1}" for j in range(3)]
        options = distractors.copy()
        correct_idx = random.randint(0, 3)
        options.insert(correct_idx, correct)

        distractor_reasons = {}
        d_idx = 0
        for opt_idx in range(4):
            if opt_idx != correct_idx:
                distractor_reasons[str(opt_idx)] = f"干擾項錯誤原因_{d_idx}"
                d_idx += 1

        questions.append({
            "question_text": f"考題_{i+1}",
            "difficulty": "easy" if i < 3 else ("medium" if i < 8 else "hard"),
            "exam_point": f"考點_{(i % 5) + 1}",
            "options": options,
            "correct_index": correct_idx,
            "explanation": f"本題考察考點_{(i % 5) + 1}，正確答案為{correct}。",
            "distractor_reasons": distractor_reasons,
        })

    context.memo["stage3_result"] = {
        "questions": questions,
        "total": num_q,
    }


@given('階段 1 已成功完成')
def step_impl(context):
    context.memo["stage1_completed"] = True
    context.memo["stage1_result"] = {
        "exam_points": [
            {"name": "考點_1", "node_id": str(uuid.uuid4()), "ratio": 50,
             "suggested_difficulty": {"easy": 30, "medium": 50, "hard": 20}},
            {"name": "考點_2", "node_id": str(uuid.uuid4()), "ratio": 50,
             "suggested_difficulty": {"easy": 30, "medium": 50, "hard": 20}},
        ],
        "point_ratio": {"考點_1": 50, "考點_2": 50},
        "difficulty_map": {
            "考點_1": {"easy": 30, "medium": 50, "hard": 20},
            "考點_2": {"easy": 30, "medium": 50, "hard": 20},
        },
    }


@given('階段 2 AI API 呼叫已重試 3 次仍失敗')
def step_impl(context):
    # Create an exam task for failure testing
    db = context.db_session

    # Find any user
    user_id = None
    for key, val in context.ids.items():
        if "@" in key:
            user_id = uuid.UUID(val)
            break

    if not user_id:
        raise KeyError("找不到任何使用者")

    subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))

    exam = Exam(
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.PENDING,
        total_questions=10,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    context.memo["current_exam_id"] = str(exam.id)
    context.memo["retry_exhausted"] = True

    # Call the API with always_fail
    token = context.jwt_helper.generate_token(str(user_id))
    response = context.api_client.post(
        f"/api/v1/exams/{exam.id}/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"fail_stage": 2, "always_fail": True, "max_retries": 3},
    )
    context.last_response = response


@given('階段 4 AI 輸出的 JSON 缺少 "explanation" 欄位')
def step_impl(context):
    # Simulate stage 4 output missing explanation
    context.memo["stage4_invalid_output"] = {
        "questions": [
            {
                "id": str(uuid.uuid4()),
                "text": "考題_1",
                "options": ["A", "B", "C", "D"],
                "answer": 0,
                "difficulty": "medium",
                "exam_point": "考點_1",
                # "explanation" is intentionally missing
                "distractor_reasons": {"1": "reason1", "2": "reason2", "3": "reason3"},
            }
        ]
    }
    context.memo["missing_field"] = "explanation"
