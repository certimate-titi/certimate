"""Given DPA 簽署狀態 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given, use_step_matcher

from app.models.institution import Institution

use_step_matcher("re")


@given(r'使用者 "(?P<email>[^"]+)" 尚未簽署機構資料處理合約')
def step_impl(context, email):
    """確保 DPA 未簽署（預設狀態，不需操作）。"""
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    institution = db.query(Institution).filter_by(admin_user_id=user_uuid).first()
    if institution:
        institution.dpa_signed_at = None
        institution.dpa_signer_name = None
        db.commit()


@given(r'使用者 "(?P<email>[^"]+)" 已簽署機構資料處理合約')
def step_impl_signed(context, email):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    institution = db.query(Institution).filter_by(admin_user_id=user_uuid).first()
    assert institution, f"找不到 {email} 管理的機構"
    institution.dpa_signed_at = datetime.now(timezone.utc)
    institution.dpa_signer_name = email
    db.commit()


@given(r'使用者 "(?P<email>[^"]+)" 已於 (?P<date>\d{4}-\d{2}-\d{2}) 簽署機構資料處理合約')
def step_impl_signed_at(context, email, date):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    institution = db.query(Institution).filter_by(admin_user_id=user_uuid).first()
    assert institution, f"找不到 {email} 管理的機構"
    signed_dt = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    institution.dpa_signed_at = signed_dt
    institution.dpa_signer_name = email
    db.commit()


use_step_matcher("parse")
