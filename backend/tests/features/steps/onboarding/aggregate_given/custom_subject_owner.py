"""Given 自訂考科 owner 相關前置條件 — Aggregate Given (PRD-033)"""

import uuid

from behave import given

from app.models.user import User, SubscriptionPlan, UserRole, UserStatus
from app.models.subject import Subject, SubjectCategory


def _ensure_user(context, email: str, onboarding_completed: bool = True) -> uuid.UUID:
    """確保使用者存在並回傳其 UUID。"""
    db = context.db_session
    if email in context.ids:
        return uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            auth_provider="email",
            subscription_plan=SubscriptionPlan.FREE,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            password_hash="$2b$12$placeholder",
            agreed_to_terms=True,
            onboarding_completed=onboarding_completed,
        )
        db.add(user)
        db.flush()
    context.ids[email] = str(user.id)
    return user.id


def _ensure_category(context, db) -> SubjectCategory:
    """確保預設 category 存在。"""
    cat = db.query(SubjectCategory).first()
    if not cat:
        cat = SubjectCategory(name="default")
        db.add(cat)
        db.flush()
    return cat


@given('使用者 "{email}" 已完成引導')
def step_already_onboarded(context, email):
    """建立已完成引導的使用者。"""
    db = context.db_session
    _ensure_user(context, email, onboarding_completed=True)
    db.commit()


@given('使用者 "{email}" 已建立自訂考科 "{subject_name}"')
def step_user_has_custom_subject(context, email, subject_name):
    """建立使用者並為其建立 scope=personal 的自訂考科。"""
    db = context.db_session
    user_uuid = _ensure_user(context, email, onboarding_completed=True)
    cat = _ensure_category(context, db)

    subj = db.query(Subject).filter_by(name=subject_name, owner_user_id=user_uuid).first()
    if not subj:
        subj = Subject(
            name=subject_name,
            category_id=cat.id,
            owner_user_id=user_uuid,
            scope="personal",
            available_questions=0,
        )
        db.add(subj)
        db.flush()
    context.ids[f"custom_subject_{subject_name}"] = str(subj.id)
    context.memo["custom_owner_email"] = email
    db.commit()


@given('使用者 "{email}" 已建立 {count:d} 個自訂考科')
def step_user_has_n_custom_subjects(context, email, count):
    """建立使用者並為其建立 N 個 scope=personal 自訂考科。"""
    db = context.db_session
    user_uuid = _ensure_user(context, email, onboarding_completed=True)
    cat = _ensure_category(context, db)

    created_ids = []
    for i in range(1, count + 1):
        sname = f"自訂考科_{email.split('@')[0]}_{i}"
        subj = Subject(
            name=sname,
            category_id=cat.id,
            owner_user_id=user_uuid,
            scope="personal",
            available_questions=0,
        )
        db.add(subj)
        db.flush()
        created_ids.append(str(subj.id))

    context.memo["custom_owner_email"] = email
    context.memo["custom_subject_ids"] = created_ids
    db.commit()
