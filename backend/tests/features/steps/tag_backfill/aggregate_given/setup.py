"""Given setup — Feature 55 Tag Backfill BDD.

建立 legacy note（含 hashtag 但 user_note_tags 為空），模擬 PR #96 前的舊資料。
"""

import uuid

from behave import given

from app.models.subject import Subject, SubjectCategory
from app.models.user import SubscriptionPlan, User, UserRole, UserStatus
from app.models.user_note import UserNote


def _ensure_category(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).filter_by(name="TestCat55").first()
    if cat is None:
        cat = SubjectCategory(name="TestCat55")
        db.add(cat)
        db.flush()
    return cat.id


def _ensure_subject(db) -> uuid.UUID:
    existing = db.query(Subject).filter_by(name="TestSubject55").first()
    if existing:
        return existing.id
    cat_id = _ensure_category(db)
    subj = Subject(name="TestSubject55", category_id=cat_id)
    db.add(subj)
    db.flush()
    return subj.id


@given('系統中已有使用者')
def step_ensure_users_from_table(context):
    """建立 background 使用者表格（含 role）。

    Table columns: email, role
    """
    from app.services.auth_service import _hash_password

    role_map = {
        "USER": UserRole.USER,
        "ADMIN": UserRole.ADMIN,
        "SUPER_ADMIN": UserRole.SUPER_ADMIN,
    }
    db = context.db_session
    if not hasattr(context, "ids"):
        context.ids = {}
    if not hasattr(context, "memo"):
        context.memo = {}

    for row in context.table:
        email = row["email"]
        role_raw = row["role"]
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            context.ids[email] = str(existing.id)
            continue
        user = User(
            email=email,
            password_hash=_hash_password("Password1!"),
            subscription_plan=SubscriptionPlan.PRO,
            role=role_map.get(role_raw, UserRole.USER),
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
        context.ids[email] = str(user.id)
    db.commit()


@given('alice 有一筆 legacy note 含 "{content}" 但 user_note_tags 為空')
def step_alice_legacy_note_without_tags(context, content):
    """建立 user_notes 筆記但故意不寫入 user_note_tags，模擬舊資料。"""
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = _ensure_subject(db)

    # 直接寫入 note，不呼叫 service（避免觸發 tag sync）
    note = UserNote(
        user_id=user_id,
        subject_id=subject_id,
        content=content.strip(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    context.memo["legacy_note_id"] = str(note.id)


@given('super@certimate.test 已登入為 SUPER_ADMIN')
def step_noop_super_admin_login(context):
    """SUPER_ADMIN 已透過 Background step 建立；此 step 為文件說明用途。"""
    pass
