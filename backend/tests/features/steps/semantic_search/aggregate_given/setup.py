"""Given setup — Feature 43 語意搜尋 + IA 遷移 BDD."""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.resource_scaffold import ResourceScaffold
from app.models.scaffold_review_schedule import ScaffoldReviewSchedule


def _ensure_alice(context):
    """確保 alice 用戶 + 資源存在，回傳 (user_id, resource)。"""
    from tests.features.steps.sm2.aggregate_given.setup import (
        _ensure_user, _ensure_resource,
    )
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    res = _ensure_resource(db, user_id, name="F43-res")
    db.commit()
    context.memo["last_user_id"] = user_id
    context.memo["last_resource"] = res
    return user_id, res


@given('用戶 alice 有 {n:d} 個 SM-2 due 鷹架')
def step_alice_has_n_due(context, n):
    user_id, res = _ensure_alice(context)
    if n == 0:
        return
    db = context.db_session
    now = datetime.now(timezone.utc)
    for i in range(n):
        sf = ResourceScaffold(
            resource_id=res.id,
            tenant_id=res.tenant_id,
            type="takeaway",
            content=f"f43-due-{i}",
            chapter_heading=f"ch-{i}",
            template_code="K-06-study",
        )
        db.add(sf)
        db.flush()
        sched = ScaffoldReviewSchedule(
            user_id=user_id,
            scaffold_id=sf.id,
            ease_factor=2.5,
            interval_days=1,
            repetitions=1,
            next_review_at=now - timedelta(hours=i + 1),
        )
        db.add(sched)
    db.commit()
    context.memo["due_count"] = n


@given('用戶 alice 有 {due_n:d} 個 due 鷹架 + {wrong_n:d} 題答錯')
def step_alice_has_due_and_wrong(context, due_n, wrong_n):
    """due 鷹架用 SM-2 排程；答錯題寫入真實 answers 表（incorrect, 未掌握）。"""
    step_alice_has_n_due(context, due_n)
    if wrong_n > 0:
        _create_wrong_answers(context, wrong_n)
    context.memo["mock_review_count"] = wrong_n


def _create_wrong_answers(context, n: int):
    """建立 n 筆 incorrect answer + Question + Exam 給 /today review_count 計算用。"""
    from datetime import datetime, timezone
    from app.models.answer import Answer
    from app.models.exam import Exam, ExamStatus
    from app.models.question import Question

    db = context.db_session
    user_id = context.memo["last_user_id"]
    res = context.memo["last_resource"]
    exam = Exam(
        user_id=user_id,
        subject_id=res.subject_id,
        status=ExamStatus.SUBMITTED,
        total_questions=n,
    )
    db.add(exam)
    db.flush()
    for i in range(n):
        q = Question(
            question_number=i + 1,
            content=f"wrong-q-{i}",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            exam_id=exam.id,
        )
        db.add(q)
        db.flush()
        ans = Answer(
            user_id=user_id,
            question_id=q.id,
            exam_id=exam.id,
            selected_answer="B",
            is_correct=False,
            answered_at=datetime.now(timezone.utc),
        )
        db.add(ans)
    db.commit()


@given('用戶 alice 有 {due_n:d} 個 due 鷹架，{wrong_n:d} 題答錯')
def step_alice_has_due_and_wrong_alt(context, due_n, wrong_n):
    """別名（中文逗號）。"""
    step_alice_has_due_and_wrong(context, due_n, wrong_n)


@given('用戶 alice 有 {n} scaffolds 含「{keyword}」')
def step_alice_has_many_scaffolds(context, n, keyword):
    """建 N 個含關鍵字 scaffold（N 解析為整數，允許 '100+' 之類）。"""
    user_id, res = _ensure_alice(context)
    # 解析 N，"100+" → 100
    try:
        count = int(str(n).rstrip("+ "))
    except Exception:
        count = 100
    db = context.db_session
    for i in range(count):
        sf = ResourceScaffold(
            resource_id=res.id,
            tenant_id=res.tenant_id,
            type="takeaway" if i % 3 else "pitfall",
            content=f"{keyword} 條目 {i}",
            chapter_heading=f"ch-{i}",
            template_code="K-06-study",
        )
        db.add(sf)
    db.commit()
    context.memo["concept_keyword"] = keyword
    context.memo["scaffolds_count"] = count


@given('Voyage API key 無效或 quota 用盡')
def step_voyage_unavailable(context):
    """Mock embedding_service.embed_texts 拋例外，觸發 fallback ILIKE。"""
    from unittest.mock import patch
    patcher = patch(
        "app.services.embedding_service.EmbeddingService.embed_texts",
        side_effect=RuntimeError("voyage API unavailable (mocked)"),
    )
    patcher.start()
    if not hasattr(context, "_cleanups"):
        context._cleanups = []
    context._cleanups.append(patcher.stop)
