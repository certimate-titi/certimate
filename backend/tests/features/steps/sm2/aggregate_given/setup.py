"""Given setup — Feature 42 SM-2 / today / concept-center BDD."""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold
from app.models.scaffold_review_schedule import ScaffoldReviewSchedule
from app.models.subject import Subject, SubjectCategory
from app.models.user import SubscriptionPlan, User, UserRole, UserStatus


def _ensure_user(db, email: str) -> uuid.UUID:
    user = db.query(User).filter_by(email=email).first()
    if user is None:
        user = User(
            email=email,
            password_hash="test-hash",
            subscription_plan=SubscriptionPlan.PRO,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
    return user.id


def _ensure_subject(db, name: str = "F42-Subject") -> uuid.UUID:
    cat = db.query(SubjectCategory).first() or SubjectCategory(name="IT")
    if cat.id is None:
        db.add(cat)
        db.flush()
    subj = db.query(Subject).filter_by(name=name).first()
    if subj is None:
        subj = Subject(name=name, category_id=cat.id)
        db.add(subj)
        db.flush()
    return subj.id


def _ensure_resource(
    db, user_id: uuid.UUID, name: str = "F42-res", status: str = "COMPLETED"
) -> Resource:
    subj_id = _ensure_subject(db)
    res = (
        db.query(Resource)
        .filter_by(user_id=user_id, name=name)
        .first()
    )
    if res is None:
        res = Resource(
            user_id=user_id,
            subject_id=subj_id,
            name=name,
            type="pdf",
            status=status,
            file_size_bytes=1024,
            gcs_path=f"{name}.pdf",
        )
        db.add(res)
        db.flush()
    return res


def _create_scaffold(
    db, resource: Resource, *, stype: str, content: str, chapter: str = "3.1"
) -> ResourceScaffold:
    sf = ResourceScaffold(
        resource_id=resource.id,
        tenant_id=resource.tenant_id,
        type=stype,
        content=content,
        chapter_heading=chapter,
        template_code="K-06-study",
    )
    db.add(sf)
    db.flush()
    return sf


@given('用戶對 scaffold "{sf_label}" 第 1 次 quality={quality}')
def step_first_review(context, sf_label, quality):
    """初次複習：建用戶 + scaffold，呼叫 sm2_service.update_review。"""
    from app.services.sm2_service import update_review

    db = context.db_session
    email = next(iter(getattr(context, "ids", {})), "alice@example.com")
    user_id = uuid.UUID(context.ids[email]) if hasattr(context, "ids") and email in context.ids else _ensure_user(db, email)
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids.setdefault(email, str(user_id))
    res = _ensure_resource(db, user_id)
    sf = _create_scaffold(db, res, stype="takeaway", content=f"{sf_label} 內容")
    db.commit()

    sched = update_review(db, user_id, sf.id, quality)
    db.commit()
    context.memo[f"sched_{sf_label}"] = sched
    context.memo["last_sched"] = sched
    context.memo["last_scaffold_id"] = sf.id
    context.memo["last_user_id"] = user_id


@given('用戶 scaffold sf-1 已 repetitions=2 (full×2)')
def step_repetitions_2(context):
    """前置：scaffold 已連 2 次 full（state = ef=2.7, interval=6, reps=2）。"""
    from app.services.sm2_service import update_review

    db = context.db_session
    email = "alice@example.com"
    user_id = _ensure_user(db, email)
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids[email] = str(user_id)
    res = _ensure_resource(db, user_id)
    sf = _create_scaffold(db, res, stype="takeaway", content="sf-1 test")
    db.commit()

    update_review(db, user_id, sf.id, "full")
    update_review(db, user_id, sf.id, "full")
    db.commit()

    context.memo["last_scaffold_id"] = sf.id
    context.memo["last_user_id"] = user_id


@given('用戶連續多次 quality=none')
def step_consecutive_none(context):
    """連續 quality=none 多次 → ease_factor 不應降低於 MIN_EASE_FACTOR(1.3)。"""
    from app.services.sm2_service import update_review

    db = context.db_session
    email = "alice@example.com"
    user_id = _ensure_user(db, email)
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids[email] = str(user_id)
    res = _ensure_resource(db, user_id, name="F42-min-ef")
    sf = _create_scaffold(db, res, stype="takeaway", content="min-ef test")
    db.commit()

    sched = None
    for _ in range(10):
        sched = update_review(db, user_id, sf.id, "none")
    db.commit()
    context.memo["last_sched"] = sched
    context.memo["last_scaffold_id"] = sf.id
    context.memo["last_user_id"] = user_id


@given('用戶 alice 有 {n:d} 個 scaffold next_review_at <= now')
def step_n_due_scaffolds(context, n):
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    res = _ensure_resource(db, user_id, name="F42-due-res")
    db.commit()

    now = datetime.now(timezone.utc)
    for i in range(n):
        sf = _create_scaffold(
            db, res, stype="takeaway", content=f"due-{i}", chapter=f"3.{i}"
        )
        sched = ScaffoldReviewSchedule(
            user_id=user_id,
            scaffold_id=sf.id,
            ease_factor=2.5,
            interval_days=1,
            repetitions=1,
            next_review_at=now - timedelta(hours=i + 1),
            last_reviewed_at=now - timedelta(days=1),
        )
        db.add(sched)
    db.commit()
    context.memo["last_user_id"] = user_id
    context.memo["due_count"] = n


@given('另有 {n:d} 個 scaffold next_review_at = {days:d} 天後')
def step_n_future_scaffolds(context, n, days):
    db = context.db_session
    user_id = context.memo["last_user_id"]
    res = _ensure_resource(db, user_id, name="F42-due-res")
    now = datetime.now(timezone.utc)
    for i in range(n):
        sf = _create_scaffold(
            db,
            res,
            stype="takeaway",
            content=f"future-{i}",
            chapter=f"future-{i}",
        )
        sched = ScaffoldReviewSchedule(
            user_id=user_id,
            scaffold_id=sf.id,
            ease_factor=2.5,
            interval_days=days,
            repetitions=2,
            next_review_at=now + timedelta(days=days),
            last_reviewed_at=now - timedelta(days=1),
        )
        db.add(sched)
    db.commit()


@given('用戶 alice 有 1 份 COMPLETED resource "{res_name}"')
def step_alice_has_completed_resource(context, res_name):
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    res = _ensure_resource(db, user_id, name=res_name, status="COMPLETED")
    db.commit()
    context.memo["last_user_id"] = user_id
    context.memo["expected_resource_id"] = str(res.id)
    context.memo["expected_resource_name"] = res_name


@given('用戶 alice 無任何資源')
def step_alice_no_resources(context):
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    # 確保乾淨：刪掉該 user 既有 resource（若 fixture session 殘留）
    db.query(Resource).filter_by(user_id=user_id).delete(synchronize_session=False)
    db.commit()
    context.memo["last_user_id"] = user_id


@given('用戶 alice 有 scaffolds 含「{keyword}」')
def step_alice_scaffolds_with_keyword(context, keyword):
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    res = _ensure_resource(db, user_id, name="F42-concept-res")
    db.commit()
    _create_scaffold(
        db,
        res,
        stype="takeaway",
        content=f"關於 {keyword} 的重點整理。",
        chapter=f"章節 {keyword}",
    )
    db.commit()
    context.memo["last_user_id"] = user_id
    context.memo["concept_keyword"] = keyword


@given('用戶有 takeaway + pitfall 兩種 scaffold 含「{keyword}」')
def step_alice_takeaway_pitfall(context, keyword):
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    res = _ensure_resource(db, user_id, name="F42-mixed-res")
    db.commit()
    _create_scaffold(
        db, res, stype="takeaway", content=f"{keyword} 重點整理", chapter="t-ch"
    )
    _create_scaffold(
        db, res, stype="pitfall", content=f"{keyword} 常見迷思警示", chapter="p-ch"
    )
    db.commit()
    context.memo["last_user_id"] = user_id
    context.memo["concept_keyword"] = keyword
