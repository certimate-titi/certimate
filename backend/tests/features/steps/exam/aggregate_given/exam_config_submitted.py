"""Given 使用者已提交合法測驗設定 (with table) — Aggregate Given"""

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

    # Parse table
    config = {}
    for row in context.table:
        config[row["欄位"]] = row["值"]

    # Parse node IDs
    node_id_strs = [n.strip() for n in config.get("選擇節點", "").split(",")]
    node_ids = []
    for nid_str in node_id_strs:
        key = f"node_{nid_str}"
        if key in context.ids:
            node_ids.append(context.ids[key])
        else:
            node_ids.append(str(uuid.UUID(int=int(nid_str))))

    total_q = int(config.get("題數", "10"))

    # Parse difficulty distribution
    diff_str = config.get("難易度分配", "")
    difficulty_dist = {"easy": 30, "medium": 50, "hard": 20}
    if diff_str:
        for part in diff_str.split():
            if ":" in part:
                level, pct = part.split(":")
                pct_val = int(pct.replace("%", ""))
                difficulty_dist[level.lower()] = pct_val

    subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))

    exam = Exam(
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.PENDING,
        total_questions=total_q,
        difficulty_distribution={
            **difficulty_dist,
            "node_ids": node_ids,
        },
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    context.ids[f"exam_{email}"] = str(exam.id)
    context.memo["current_exam_id"] = str(exam.id)
    context.memo["current_user_email"] = email
    context.memo["difficulty_distribution"] = difficulty_dist
    context.memo["total_questions"] = total_q
