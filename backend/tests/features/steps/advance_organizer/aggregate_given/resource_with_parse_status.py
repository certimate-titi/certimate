"""Given 用戶擁有資源且解析狀態 — Feature 41 advance_organizer BDD."""

import uuid

from behave import given

from app.models.resource import Resource
from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob
from app.models.subject import Subject, SubjectCategory
from app.models.user import SubscriptionPlan, User, UserRole, UserStatus


def _ensure_user(db, email: str, plan: str = "PRO") -> str:
    """建立或取得用戶，回傳 user_id 字串。"""
    plan_map = {
        "FREE": SubscriptionPlan.FREE,
        "PRO": SubscriptionPlan.PRO,
        "PRO_PLUS": SubscriptionPlan.PRO_PLUS,
    }
    user = db.query(User).filter_by(email=email).first()
    if user is None:
        user = User(
            email=email,
            password_hash="test-hash",
            subscription_plan=plan_map.get(plan, SubscriptionPlan.PRO),
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
    return str(user.id)


@given('已存在 PRO 用戶 "{email}"')
def step_pro_user_exists(context, email):
    """建立或確保 PRO 用戶存在，並記錄到 context.ids。"""
    db = context.db_session
    user_id = _ensure_user(db, email, plan="PRO")
    db.commit()
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids[email] = user_id


def _ensure_subject(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).first()
    if cat is None:
        cat = SubjectCategory(name="IT")
        db.add(cat)
        db.flush()
    subj = db.query(Subject).filter_by(name="Feature41-Subject").first()
    if subj is None:
        subj = Subject(name="Feature41-Subject", category_id=cat.id)
        db.add(subj)
        db.flush()
    return subj.id


@given('用戶 "{email}" 擁有資源 "{res_name}" 解析狀態為 "success"')
def step_resource_success(context, email, res_name):
    db = context.db_session
    # 確保用戶存在（若 Background 已建則取用）
    if not hasattr(context, "ids"):
        context.ids = {}
    if email not in context.ids:
        context.ids[email] = _ensure_user(db, email)
    user_id = uuid.UUID(context.ids[email])
    subject_id = _ensure_subject(db)

    resource = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name=res_name,
        type="pdf",
        status="COMPLETED",
        file_size_bytes=2048,
        gcs_path=f"{res_name}.pdf",
        parsed_markdown="# 3.1 折現率\n\n折現率是反向利率計算。",
        detected_content_type="study_material",
    )
    db.add(resource)
    db.flush()

    job = ResourceParseJob(
        resource_id=resource.id,
        tenant_id=resource.tenant_id,
        status=ParseJobStatus.SUCCESS.value,
        gemini_model="gemini-2.5-pro",
    )
    db.add(job)
    db.commit()
    db.refresh(resource)

    context.memo["last_resource_id"] = str(resource.id)
    context.memo["last_resource_obj"] = resource


from behave import use_step_matcher

use_step_matcher("re")


@given(r'resource gcs_path="(?P<gcs>[^"]*)" / dct="(?P<dct>[^"]*)" / yt="(?P<yt>[^"]*)"')
def step_resource_routing_given(context, gcs, dct, yt):
    """建立 Resource stub 供 _select_prompt_template 路由測試（支援空字串欄位）。"""

    class _ResourceStub:
        """輕量 stub，避免 SQLAlchemy instrumentation 問題。"""
        def __init__(self, gcs_path, youtube_url, detected_content_type, name):
            self.gcs_path = gcs_path
            self.youtube_url = youtube_url
            self.detected_content_type = detected_content_type
            self.name = name

    r = _ResourceStub(
        gcs_path=gcs if gcs else None,
        youtube_url=yt if yt else None,
        detected_content_type=dct if dct else None,
        name=gcs or "virtual.pdf",
    )
    context.memo["routing_resource"] = r


use_step_matcher("parse")
