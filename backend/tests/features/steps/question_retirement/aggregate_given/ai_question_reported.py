"""Given AI 題被多位使用者回報品質問題 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.content_report import ContentReport
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.models.user import User, UserStatus, SubscriptionPlan
from app.repositories.subject_repository import SubjectRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import _hash_password


@given('一題 AI 題被 {count:d} 位不同使用者回報品質問題')
def step_impl(context, count):
    db = context.db_session
    now = datetime.now(timezone.utc)

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name("證券商業務員")

    # 取得第一位已有的使用者
    user_repo = UserRepository(db)
    first_user = user_repo.find_by_email("alice@example.com")

    # 建立 Exam + AI 題
    exam = Exam(
        user_id=first_user.id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED,
        total_questions=1,
    )
    db.add(exam)
    db.flush()

    q = Question(
        exam_id=exam.id,
        question_number=1,
        content="AI 生成題目：品質回報測試",
        option_a="選項 A",
        option_b="選項 B",
        option_c="選項 C",
        option_d="選項 D",
        correct_answer="A",
        source_type="ai_generated",
        quality_flag="ok",
    )
    db.add(q)
    db.flush()

    # 建立 N 筆 content_reports
    for i in range(count):
        reporter = User(
            email=f"reporter{i}@example.com",
            password_hash=_hash_password("Password1!"),
            subscription_plan=SubscriptionPlan.FREE,
            status=UserStatus.ACTIVE,
            agreed_to_terms=True,
        )
        saved_reporter = user_repo.save(reporter)

        report = ContentReport(
            report_ref=f"RPT-{uuid.uuid4().hex[:8]}",
            reporter_id=str(saved_reporter.id),
            report_type="quality_issue",
            target_type="question",
            target_id=str(q.id),
            status="pending",
        )
        db.add(report)

    db.commit()

    context.memo["ai_question_ids"] = [str(q.id)]
    context.memo["current_question_id"] = str(q.id)
    context.memo["report_count"] = count
