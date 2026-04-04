"""Given 放榜通知相關前置狀態 — Aggregate Given"""

import uuid
from datetime import date, datetime, timedelta, timezone

from behave import given
from app.models.exam import Exam, ExamStatus
from app.models.learning_journey import LearningJourney
from app.models.question import Question
from app.repositories.learning_journey_repository import LearningJourneyRepository
from app.repositories.subject_repository import SubjectRepository


@given('使用者 "{email}" 的科目 "{subject_name}" 放榜日為今天')
def step_result_date_today(context, email, subject_name):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)

    lj_repo = LearningJourneyRepository(db)
    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    if journey:
        journey.result_date = date.today()
        db.commit()
    else:
        journey = LearningJourney(
            user_id=user_id,
            subject_id=subject.id,
            result_date=date.today(),
        )
        saved = lj_repo.save(journey)
        context.memo["current_journey_id"] = str(saved.id)

    context.memo[f"learning_journey_{email}_{subject_name}"] = str(journey.id)


@given('使用者 "{email}" 的放榜通知已發送 {days:d} 天')
def step_notification_sent_days_ago(context, email, days):
    """放榜通知已發 N 天 → 將 result_date 設為 N 天前。"""
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name("證券商業務員")

    lj_repo = LearningJourneyRepository(db)
    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    if journey:
        journey.result_date = date.today() - timedelta(days=days)
        db.commit()
        context.memo["current_journey_id"] = str(journey.id)

    context.memo["notification_sent_days_ago"] = days
    context.memo["notification_email"] = email


@given('使用者尚未回覆放榜結果')
def step_no_reply(context):
    # exam_result_status 預設為 NULL，不需額外操作
    pass


@given('使用者 "{email}" 確認科目 "{subject_name}" 未考取')
def step_confirmed_failed(context, email, subject_name):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)

    lj_repo = LearningJourneyRepository(db)
    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    if journey:
        journey.exam_result_status = "failed"
        db.commit()
    else:
        journey = LearningJourney(
            user_id=user_id,
            subject_id=subject.id,
            exam_result_status="failed",
        )
        lj_repo.save(journey)

    context.memo[f"learning_journey_{email}_{subject_name}"] = str(journey.id)
    context.memo["current_journey_id"] = str(journey.id)
    context.memo["confirm_email"] = email
    context.memo["confirm_subject"] = subject_name


@given('使用者 "{email}" 於 {days:d} 天前確認考取科目 "{subject_name}"')
def step_confirmed_passed_days_ago(context, email, days, subject_name):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)
    today = date.today()

    lj_repo = LearningJourneyRepository(db)
    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    if not journey:
        journey = LearningJourney(user_id=user_id, subject_id=subject.id)
        db.add(journey)
        db.flush()

    journey.exam_result_status = "passed"
    journey.data_expiry_date = today - timedelta(days=days) + timedelta(days=7)
    db.commit()

    # 建立 AI 題（供退場測試）
    exam = Exam(
        user_id=user_id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED,
        total_questions=3,
    )
    db.add(exam)
    db.flush()

    ai_ids = []
    for i in range(3):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"AI 題 {i + 1}（考取後測試）",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            source_type="ai_generated",
            quality_flag="ok",
        )
        db.add(q)
        db.flush()
        ai_ids.append(str(q.id))

    db.commit()
    context.memo["ai_question_ids"] = ai_ids
    context.memo["ai_subject_id"] = str(subject.id)
    context.memo[f"learning_journey_{email}_{subject_name}"] = str(journey.id)
    context.memo["current_journey_id"] = str(journey.id)


@given('使用者 "{email}" 於 {days:d} 天前確認不再報考科目 "{subject_name}"')
def step_confirmed_quit_days_ago(context, email, days, subject_name):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)
    today = date.today()

    lj_repo = LearningJourneyRepository(db)
    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    if not journey:
        journey = LearningJourney(user_id=user_id, subject_id=subject.id)
        db.add(journey)
        db.flush()

    journey.exam_result_status = "quit"
    journey.data_expiry_date = today - timedelta(days=days) + timedelta(days=30)
    db.commit()

    # 建立 AI 題（供退場測試）
    exam = Exam(
        user_id=user_id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED,
        total_questions=3,
    )
    db.add(exam)
    db.flush()

    ai_ids = []
    for i in range(3):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"AI 題 {i + 1}（不再報考測試）",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            source_type="ai_generated",
            quality_flag="ok",
        )
        db.add(q)
        db.flush()
        ai_ids.append(str(q.id))

    db.commit()
    context.memo["ai_question_ids"] = ai_ids
    context.memo["ai_subject_id"] = str(subject.id)
    context.memo[f"learning_journey_{email}_{subject_name}"] = str(journey.id)
    context.memo["current_journey_id"] = str(journey.id)


@given('使用者 "{email}" 從未使用過 AI 出題功能')
def step_never_used_ai(context, email):
    # 預設就沒有 AI 出題紀錄，存 email 供後續使用
    context.memo["ai_consent_email"] = email


@given('本次退場掃描偵測到 {count} 題符合退場條件')
def step_bulk_retirement(context, count):
    db = context.db_session
    count_int = int(count.replace(",", ""))

    user_repo = __import__("app.repositories.user_repository", fromlist=["UserRepository"]).UserRepository(db)
    user = user_repo.find_by_email("alice@example.com")
    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name("證券商業務員")

    now = datetime.now(timezone.utc)

    exam = Exam(
        user_id=user.id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED,
        total_questions=count_int,
    )
    db.add(exam)
    db.flush()

    for i in range(count_int):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"批量 AI 題 {i + 1}",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            source_type="ai_generated",
            expires_at=now - timedelta(days=10),  # 已過期
        )
        db.add(q)
    db.commit()

    context.memo["bulk_retirement_count"] = count_int
