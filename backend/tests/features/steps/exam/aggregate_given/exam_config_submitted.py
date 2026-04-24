"""Given 使用者已提交合法測驗設定 (with table) — Aggregate Given"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.historical_exam import HistoricalExam
from app.models.question import Question
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

    diff_dist = {
        **difficulty_dist,
        "node_ids": node_ids,
    }
    exam_mode = config.get("exam_mode")
    if exam_mode:
        diff_dist["exam_mode"] = exam_mode.strip()

    # historical_only 模式：為所選節點補 seed 考古題，讓 service 可抽題
    if exam_mode and exam_mode.strip() == "historical_only":
        he = db.query(HistoricalExam).filter_by(exam_code="AIGEN_TEST").first()
        if not he:
            he = HistoricalExam(
                exam_code="AIGEN_TEST",
                subject_code="aigen_default",
                exam_name="AI Gen Test 考古題",
                subject_name="AI Gen Test",
            )
            db.add(he)
            db.commit()
            db.refresh(he)
        seed_count = max(total_q, 10)
        for idx, nid_str in enumerate(node_ids):
            for i in range(seed_count):
                q = Question(
                    historical_exam_id=he.id,
                    node_id=uuid.UUID(nid_str),
                    question_number=(idx + 1) * 10000 + i + 1,
                    content=f"考古題 node{idx+1} #{i + 1}",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="A",
                    source_type="historical",
                    quality_flag="ok",
                    historical_source=he.exam_name,
                )
                db.add(q)
        db.commit()

    exam = Exam(
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.PENDING,
        total_questions=total_q,
        difficulty_distribution=diff_dist,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    context.ids[f"exam_{email}"] = str(exam.id)
    context.memo["current_exam_id"] = str(exam.id)
    context.memo["current_user_email"] = email
    context.memo["difficulty_distribution"] = difficulty_dist
    context.memo["total_questions"] = total_q
