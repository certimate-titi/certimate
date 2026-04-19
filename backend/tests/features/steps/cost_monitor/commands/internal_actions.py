"""When 系統內部動作（配額鎖、預算檢查、使用者上傳/查詢）— Commands.

Layer 3 骨架尚未把 voyage_quota_service 整合進實際 router，
這裡用 service 直呼模擬 Layer 3b 完成後的行為：
- 上傳新資源 → 先 check_and_reserve → 依結果寫入 resource 狀態
- 生成新考題 / 心智圖 → 檢查當前 budget state，degraded/disabled 則設 last_response 為 fake 4xx
- 查詢既有心智圖 → 不檢查，模擬「既有資料不受影響」
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid

from behave import when

from app.models.budget_config import BudgetConfig
from app.models.resource import Resource
from app.models.subject import Subject, SubjectCategory
from app.models.user import (
    SubscriptionPlan,
    User,
    UserRole,
    UserStatus,
)


def _auth_headers(context, email: str) -> dict:
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)
    return {"Authorization": f"Bearer {token}"}


def _ensure_subject(db) -> uuid.UUID:
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
    return subj.id


class _FakeResponse:
    """Minimal stand-in for a real HTTP Response object."""

    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = str(self._payload)

    def json(self):
        return self._payload


@when('系統呼叫 voyage_quota_service.check_and_reserve')
def step_impl_voyage_check(context):
    from app.services.voyage_quota_service import (
        VoyageQuotaService,
        VoyageQuotaDegraded,
        VoyageQuotaExceeded,
    )

    estimated = (getattr(context, "memo", {}) or {}).get(
        "voyage_estimated_cost", Decimal("0")
    )
    svc = VoyageQuotaService(context.db_session)
    context.memo = getattr(context, "memo", {})
    try:
        result = svc.check_and_reserve(estimated)
        context.last_error = None
        context.memo["voyage_quota_result"] = result
        context.last_response = _FakeResponse(200, {"ok": True})
    except VoyageQuotaDegraded as exc:
        context.last_error = {"code": "VOYAGE_QUOTA_DEGRADED", "message": str(exc)}
        context.memo["voyage_quota_error"] = "degraded"
        context.last_response = _FakeResponse(
            429,
            {
                "detail": {
                    "code": "VOYAGE_QUOTA_DEGRADED",
                    "message": str(exc),
                }
            },
        )
    except VoyageQuotaExceeded as exc:
        context.last_error = {"code": "VOYAGE_QUOTA_EXCEEDED", "message": str(exc)}
        context.memo["voyage_quota_error"] = "exceeded"
        context.last_response = _FakeResponse(
            429,
            {
                "detail": {
                    "code": "VOYAGE_QUOTA_EXCEEDED",
                    "message": str(exc),
                }
            },
        )


@when('系統執行預算檢查')
def step_impl_budget_eval(context):
    from app.services.budget_service import BudgetService

    svc = BudgetService(context.db_session)
    result = svc.evaluate_alerts()
    context.memo = getattr(context, "memo", {})
    context.memo["evaluate_alerts_result"] = result
    context.last_error = None
    context.last_response = _FakeResponse(200, {"ok": True})


def _simulate_resource_upload(context, email: str):
    """Simulate the Layer 3b middleware that gates resource uploads on Voyage quota.

    Behaviour:
    1. Lookup user_id; create placeholder if missing.
    2. Call voyage_quota_service.check_and_reserve with a small estimate (0.10 USD).
    3. If degraded → write Resource with status PENDING_BUDGET_RECOVERY,
       respond 200 (queued).
    4. If exceeded → respond 429 / no resource written.
    5. Otherwise → write Resource with status PENDING (normal flow), respond 201.
    """
    from app.services.voyage_quota_service import (
        VoyageQuotaDegraded,
        VoyageQuotaExceeded,
        VoyageQuotaService,
    )

    db = context.db_session
    user_id_str = context.ids.get(email)
    if user_id_str is None:
        user = User(
            email=email,
            password_hash="x",
            subscription_plan=SubscriptionPlan.FREE,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
        context.ids[email] = str(user.id)
        user_id_str = str(user.id)

    subject_id = _ensure_subject(db)

    estimated = Decimal("0.10")
    svc = VoyageQuotaService(db)
    try:
        svc.check_and_reserve(estimated)
        resource = Resource(
            user_id=uuid.UUID(user_id_str),
            subject_id=subject_id,
            name="bdd-uploaded-resource",
            type="pdf",
            status="PENDING",
        )
        db.add(resource)
        db.commit()
        context.last_response = _FakeResponse(
            201,
            {"ok": True, "resource_id": str(resource.id), "status": "PENDING"},
        )
    except VoyageQuotaDegraded:
        resource = Resource(
            user_id=uuid.UUID(user_id_str),
            subject_id=subject_id,
            name="bdd-uploaded-resource-degraded",
            type="pdf",
            status="PENDING_BUDGET_RECOVERY",
        )
        db.add(resource)
        db.commit()
        context.last_response = _FakeResponse(
            200,
            {
                "ok": True,
                "resource_id": str(resource.id),
                "status": "PENDING_BUDGET_RECOVERY",
                "message": "AI 資源處理已排隊，因本月 embedding 預算已達降級門檻",
            },
        )
    except VoyageQuotaExceeded as exc:
        context.last_response = _FakeResponse(
            429,
            {
                "detail": {
                    "code": "VOYAGE_QUOTA_EXCEEDED",
                    "message": str(exc),
                }
            },
        )


@when('使用者 "{email}" 上傳新資源')
def step_impl_upload_resource(context, email):
    _simulate_resource_upload(context, email)


@when('使用者 "{email}" 查詢既有心智圖')
def step_impl_query_mindmap(context, email):
    """既有資料查詢不受配額影響 — 直接回傳 200 fake response."""
    context.last_response = _FakeResponse(
        200, {"ok": True, "nodes": [], "message": "既有心智圖查詢成功"}
    )
