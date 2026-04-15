"""Given 其他情境 Given — pending resources, BQ billing, mindmap ready, ..."""

from datetime import datetime, timezone
from decimal import Decimal

from behave import given

from app.models.resource import Resource
from app.models.user import User


def _get_any_user_id(db) -> str | None:
    u = db.query(User).first()
    return str(u.id) if u else None


@given('BigQuery Billing Export 有以下資料：')
def step_impl_bq_data(context):
    """The fake GcpBillingService returns fixed stub data.
    This step is informational — Layer 3b will hook into a configurable fake.
    """
    context.memo = getattr(context, "memo", {})
    context.memo["bq_stub_rows"] = [dict(row.as_dict()) for row in context.table]


@given('有 {count:d} 筆資源狀態為 "{status}"')
def step_impl_pending_resources(context, count, status):
    db = context.db_session
    user_id = _get_any_user_id(db)
    if user_id is None:
        # Create a placeholder user
        from app.models.user import SubscriptionPlan, UserRole, UserStatus
        u = User(
            email="pending_owner@test.internal",
            password_hash="x",
            subscription_plan=SubscriptionPlan.FREE,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(u)
        db.flush()
        user_id = str(u.id)

    # resources 需要 subject_id — 抓第一個 subject 或建一個
    from app.models.subject import Subject, SubjectCategory
    subj = db.query(Subject).first()
    if subj is None:
        cat = db.query(SubjectCategory).first()
        if cat is None:
            cat = SubjectCategory(name="BDD Category")
            db.add(cat)
            db.flush()
        subj = Subject(name="BDD Test Subject", category_id=cat.id)
        db.add(subj)
        db.flush()

    for i in range(count):
        r = Resource(
            user_id=user_id,
            subject_id=subj.id,
            name=f"pending-resource-{i}",
            type="pdf",
            status=status,
        )
        db.add(r)
    db.commit()


@given('既有知識心智圖已完成 embedding')
def step_impl_mindmap_ready(context):
    # Informational — no DB action needed for the Layer 3 skeleton.
    pass
