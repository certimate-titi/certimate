"""Given 各階段輸入/狀態設定 — Aggregate Given"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus
from app.repositories.exam_repository import ExamRepository


@given('階段 1 已輸出含 {n:d} 個考點、各 {q:d} 題的考綱')
def step_stage1_output(context, n, q):
    """Record stage 1 output for stage 2 input."""
    exam_points = []
    for i in range(n):
        exam_points.append({
            "name": f"考點_{i+1}",
            "node_id": str(uuid.uuid4()),
            "ratio": 100 // n,
            "suggested_difficulty": {"easy": 30, "medium": 50, "hard": 20},
        })

    context.memo["stage_1_output"] = {
        "exam_points": exam_points,
        "point_ratio": {p["name"]: p["ratio"] for p in exam_points},
        "difficulty_map": {p["name"]: p["suggested_difficulty"] for p in exam_points},
    }
    context.memo["total_questions"] = n * q


@given('階段 2 已輸出 {n:d} 題原始考題')
def step_stage2_output(context, n):
    """Record stage 2 output for stage 3 input."""
    questions = []
    difficulties = ["easy"] * 3 + ["medium"] * 5 + ["hard"] * 2
    for i in range(n):
        questions.append({
            "question_text": f"考題第{i+1}題",
            "correct_answer": f"正確答案_{i+1}",
            "difficulty": difficulties[i % len(difficulties)],
            "exam_point": f"考點_{(i % 5) + 1}",
        })

    context.memo["stage_2_output"] = {
        "questions": questions,
        "total": n,
    }


@given('階段 3 已輸出 {n:d} 題完整考題')
def step_stage3_output(context, n):
    """Record stage 3 output for stage 4 input."""
    import random
    questions = []
    for i in range(n):
        correct_idx = random.randint(0, 3)
        options = [f"選項_{chr(65+j)}_{i+1}" for j in range(4)]
        options[correct_idx] = f"正確答案_{i+1}"

        distractor_reasons = {}
        for opt_idx in range(4):
            if opt_idx != correct_idx:
                distractor_reasons[str(opt_idx)] = f"干擾項錯誤原因_{opt_idx}"

        questions.append({
            "question_text": f"考題第{i+1}題",
            "difficulty": ["easy", "medium", "hard"][i % 3],
            "exam_point": f"考點_{(i % 5) + 1}",
            "options": options,
            "correct_index": correct_idx,
            "explanation": f"本題考察考點_{(i % 5) + 1}，正確答案為正確答案_{i+1}。",
            "distractor_reasons": distractor_reasons,
        })

    context.memo["stage_3_output"] = {
        "questions": questions,
        "total": n,
    }


@given('階段 1 已成功完成')
def step_stage1_completed(context):
    """Mark stage 1 as completed."""
    context.memo["stage_1_completed"] = True
    # Ensure we have an exam
    if "current_exam_id" not in context.memo:
        # Create a default exam for retry tests
        db = context.db_session
        subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))
        # Find first user
        user_id = None
        for key, val in context.ids.items():
            if '@' in key:
                user_id = uuid.UUID(val)
                break
        if not user_id:
            user_id = uuid.uuid4()

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
        context.ids["current_exam"] = str(exam.id)


@given('階段 2 AI API 呼叫已重試 {n:d} 次仍失敗')
def step_stage2_retries_exhausted(context, n):
    """Mark stage 2 retries as exhausted."""
    context.memo["stage_2_retries_exhausted"] = True
    context.memo["retry_count"] = n

    # Ensure we have an exam
    if "current_exam_id" not in context.memo:
        db = context.db_session
        subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))
        user_id = None
        for key, val in context.ids.items():
            if '@' in key:
                user_id = uuid.UUID(val)
                break
        if not user_id:
            user_id = uuid.uuid4()

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
        context.ids["current_exam"] = str(exam.id)


@given('階段 4 AI 輸出的 JSON 缺少 "explanation" 欄位')
def step_stage4_missing_field(context):
    """Set up stage 4 output missing a field."""
    context.memo["stage_4_missing_field"] = "explanation"
    context.memo["stage_4_invalid_output"] = {
        "id": str(uuid.uuid4()),
        "text": "sample question",
        "options": ["A", "B", "C", "D"],
        "answer": 0,
        "difficulty": "medium",
        "exam_point": "test",
        # "explanation" is intentionally missing
        "distractor_reasons": {"1": "reason1", "2": "reason2", "3": "reason3"},
    }
