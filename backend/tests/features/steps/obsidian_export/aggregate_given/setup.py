"""Given setup — Feature 53 Obsidian Export BDD."""

import uuid
from datetime import date, timedelta

from behave import given

from app.models.learning_journey import LearningJourney, LearningMode, SelfAssessedLevel
from app.models.subject import Subject, SubjectCategory
from app.models.user import SubscriptionPlan, User, UserRole, UserStatus
from app.models.user_note import UserNote


def _ensure_user(db, email: str, plan: str = "FREE") -> uuid.UUID:
    plan_map = {
        "FREE": SubscriptionPlan.FREE,
        "PRO": SubscriptionPlan.PRO,
        "PRO_PLUS": SubscriptionPlan.PRO_PLUS,
    }
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        return existing.id
    user = User(
        email=email,
        password_hash="test-hash",
        subscription_plan=plan_map.get(plan, SubscriptionPlan.FREE),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return user.id


def _ensure_category(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).filter_by(name="TestCat53").first()
    if cat is None:
        cat = SubjectCategory(name="TestCat53")
        db.add(cat)
        db.flush()
    return cat.id


def _ensure_subject(db, name: str) -> Subject:
    existing = db.query(Subject).filter_by(name=name).first()
    if existing:
        return existing
    cat_id = _ensure_category(db)
    subj = Subject(name=name, category_id=cat_id)
    db.add(subj)
    db.flush()
    return subj


def _make_journey(
    db,
    user_id: uuid.UUID,
    subject_id: uuid.UUID,
    exam_date: date | None,
) -> LearningJourney:
    """建立或更新學習旅程，回傳 LearningJourney ORM 物件。"""
    existing = (
        db.query(LearningJourney)
        .filter_by(user_id=user_id, subject_id=subject_id)
        .first()
    )
    if existing:
        existing.exam_date = exam_date
        db.flush()
        return existing
    journey = LearningJourney(
        user_id=user_id,
        subject_id=subject_id,
        exam_date=exam_date,
        self_assessed_level=SelfAssessedLevel.BEGINNER,
        learning_mode=LearningMode.STANDARD,
    )
    db.add(journey)
    db.flush()
    return journey


# ── Background steps（re-use from feature 50 via note_hashtags）──────────────
# Note: 已有 "已存在科目 {name} subject_id 存於 memo[subject_id]" from f50 setup
# 如果 Background 步驟與既有 step 衝突，新 feature 直接共用；
# 本檔只補充 obsidian-export 特有的 Given steps。

@given('alice 已有考後 31 天的學習旅程 journey_id 存於 memo["journey_id"]')
def step_alice_journey_post_exam_31(context):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    exam_date = date.today() - timedelta(days=31)
    journey = _make_journey(db, user_id, subject_id, exam_date)
    db.commit()
    context.memo["journey_id"] = str(journey.id)


@given('alice 已有未來考試的學習旅程（考試日 90 天後）')
def step_alice_journey_future_exam(context):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    exam_date = date.today() + timedelta(days=90)
    journey = _make_journey(db, user_id, subject_id, exam_date)
    db.commit()
    context.memo["journey_id"] = str(journey.id)


@given('bob 沒有任何筆記且已有考後 31 天的學習旅程')
def step_bob_no_notes_post_exam_journey(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["bob@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    exam_date = date.today() - timedelta(days=31)
    _make_journey(db, user_id, subject_id, exam_date)
    db.commit()
