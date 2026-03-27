"""Given 使用者已提交合法測驗設定 — Aggregate Given"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus
from app.repositories.exam_repository import ExamRepository


@given('使用者 "{email}" 已提交合法測驗設定：')
def step_impl(context, email):
    db = context.db_session
    repo = ExamRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    user_id = uuid.UUID(context.ids[email])

    subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))

    # Parse config from table
    config = {}
    node_ids = []
    question_count = 10
    difficulty_dist = {}

    for row in context.table:
        field = row["欄位"]
        value = row["值"]

        if field == "選擇節點":
            node_ids = [nid.strip() for nid in value.split(",")]
        elif field == "題數":
            question_count = int(value)
        elif field == "難易度分配":
            # Parse "Easy:30% Medium:50% Hard:20%"
            for part in value.split():
                if ":" in part:
                    level, pct = part.split(":")
                    pct = pct.replace("%", "")
                    difficulty_dist[level.lower()] = int(pct)

    # Convert node_ids to UUID strings
    node_uuid_strs = []
    for nid in node_ids:
        key = f"node_{nid}"
        if key in context.ids:
            node_uuid_strs.append(context.ids[key])
        else:
            node_uuid_strs.append(str(uuid.UUID(int=int(nid))))

    exam = Exam(
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.PENDING,
        total_questions=question_count,
        difficulty_distribution={
            "easy": difficulty_dist.get("easy", 30),
            "medium": difficulty_dist.get("medium", 50),
            "hard": difficulty_dist.get("hard", 20),
            "node_ids": node_uuid_strs,
        },
    )
    repo.save(exam)
    context.ids["current_exam"] = str(exam.id)
    context.memo["current_exam_id"] = str(exam.id)
    context.memo["current_user_email"] = email
    context.memo["exam_config"] = {
        "node_ids": node_uuid_strs,
        "question_count": question_count,
        "difficulty_distribution": difficulty_dist,
    }
