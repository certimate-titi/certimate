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
    """Inject BigQuery Billing Export test data into GcpBillingService.

    Feature table format:
        | service              | cost_usd | billing_date |
        | Cloud Run            | 120.00   | 2026-04-01   |
        | Cloud SQL            | 180.25   | 2026-04-01   |
        ...
    """
    from app.services.gcp_billing_service import set_test_services

    context.memo = getattr(context, "memo", {})

    # 轉換 feature table 資料格式
    services_list = []
    for row in context.table:
        services_list.append({
            "service_name": row.get("service") or row.get("service_name"),
            "cost_usd": Decimal(row.get("cost_usd", "0")),
        })

    # 注入到 GcpBillingService
    set_test_services(services_list)
    context.memo["bq_services"] = services_list


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
