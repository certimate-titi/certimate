"""Then 自訂考科斷言 — Aggregate Then & ReadModel Then (PRD-033)"""

import uuid

from behave import then

from app.models.subject import Subject


@then('新 subject 的 owner_user_id 應為 u1 的 UUID')
def step_owner_is_u1(context):
    """驗證最近建立的 subject.owner_user_id 等於 custom_owner_email 對應的 user UUID。"""
    db = context.db_session
    db.expire_all()

    email = context.memo.get("custom_owner_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_uuid = uuid.UUID(context.ids[email])

    subject_name = context.memo.get("last_created_subject_name")
    assert subject_name, "找不到最近建立的 subject name（last_created_subject_name 未設置）"

    subj = db.query(Subject).filter_by(
        name=subject_name, owner_user_id=user_uuid
    ).first()
    assert subj is not None, (
        f"找不到 owner={user_uuid} 的 subject '{subject_name}'"
    )
    assert subj.owner_user_id == user_uuid, (
        f"owner_user_id 應為 {user_uuid}，實際為 {subj.owner_user_id}"
    )


@then('新 subject 的 scope 應為 "{expected_scope}"')
def step_scope_is(context, expected_scope):
    """驗證最近建立的 subject.scope 等於期望值。"""
    db = context.db_session
    db.expire_all()

    email = context.memo.get("custom_owner_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_uuid = uuid.UUID(context.ids[email])

    subject_name = context.memo.get("last_created_subject_name")
    assert subject_name, "找不到最近建立的 subject name"

    subj = db.query(Subject).filter_by(
        name=subject_name, owner_user_id=user_uuid
    ).first()
    assert subj is not None, f"找不到 subject '{subject_name}'"
    assert subj.scope == expected_scope, (
        f"scope 應為 '{expected_scope}'，實際為 '{subj.scope}'"
    )


@then('回應清單不應包含 "{subject_name}"')
def step_response_excludes(context, subject_name):
    """驗證 API 回應不包含指定科目名稱。"""
    response = context.last_response
    assert response is not None, "找不到 last_response"
    assert response.status_code == 200, (
        f"預期 200，實際 {response.status_code}: {response.text}"
    )
    data = response.json()

    # 支援 {"subjects": [...]} 或 {"categories": [{subjects: [...]}, ...]}
    all_names = set()
    for subj in data.get("subjects", []):
        all_names.add(subj.get("name"))
    for cat in data.get("categories", []):
        for subj in cat.get("subjects", []):
            all_names.add(subj.get("name"))

    assert subject_name not in all_names, (
        f"回應不應包含 '{subject_name}'，但找到了（清單: {all_names}）"
    )


@then("回應清單只應包含 scope=platform AND owner_user_id IS NULL 的科目")
def step_response_only_platform(context):
    """驗證回應中所有科目都是 platform scope 且 owner 為 NULL。"""
    db = context.db_session
    response = context.last_response
    assert response is not None, "找不到 last_response"
    assert response.status_code == 200, (
        f"預期 200，實際 {response.status_code}: {response.text}"
    )
    data = response.json()

    subject_ids = []
    for subj in data.get("subjects", []):
        subject_ids.append(subj.get("id"))
    for cat in data.get("categories", []):
        for subj in cat.get("subjects", []):
            subject_ids.append(subj.get("id"))

    for sid in subject_ids:
        subj = db.query(Subject).filter_by(id=uuid.UUID(sid)).first()
        if subj is None:
            continue
        assert subj.scope == "platform", (
            f"subject {subj.name} 的 scope={subj.scope}，應為 platform"
        )
        assert subj.owner_user_id is None, (
            f"subject {subj.name} 的 owner_user_id={subj.owner_user_id}，應為 NULL"
        )


@then('應回應 {count:d} 筆 subjects（皆為 u1 擁有）')
def step_mine_count(context, count):
    """驗證 /subjects/mine 回傳指定數量的 subjects 且都屬於 custom_owner。"""
    response = context.last_response
    assert response is not None, "找不到 last_response"
    assert response.status_code == 200, (
        f"預期 200，實際 {response.status_code}: {response.text}"
    )
    data = response.json()
    subjects = data.get("subjects", [])
    assert len(subjects) == count, (
        f"預期 {count} 筆 subjects，實際 {len(subjects)}: {[s.get('name') for s in subjects]}"
    )
