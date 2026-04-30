"""When 自訂考科相關指令 — Commands (PRD-033)"""

from behave import when


@when('使用者透過 SubjectPickerModal 建立自訂考科 "{subject_name}"')
def step_create_custom_subject(context, subject_name):
    """呼叫 POST /api/v1/subjects 建立自訂考科。"""
    # 取得 owner email（優先 custom_owner_email，否則找第一個 @ key）
    email = context.memo.get("custom_owner_email") or context.memo.get("current_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/subjects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject_name": subject_name,
        },
    )
    context.last_response = response
    context.memo["last_created_subject_name"] = subject_name
    context.memo["custom_owner_email"] = email


@when('使用者 "{email}" 呼叫 GET /api/v1/subjects/available')
def step_get_available_subjects(context, email):
    """以指定使用者身分呼叫 GET /api/v1/subjects/available。"""
    # 確保 u2 存在
    if email not in context.ids:
        from app.models.user import User, SubscriptionPlan, UserRole, UserStatus
        db = context.db_session
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
                onboarding_completed=True,
            )
            db.add(user)
            db.commit()
        context.ids[email] = str(user.id)

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/subjects/available",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('呼叫 GET /api/v1/subjects/mine')
def step_get_mine_subjects(context):
    """以 custom_owner_email 身分呼叫 GET /api/v1/subjects/mine。"""
    email = context.memo.get("custom_owner_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/subjects/mine",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when("呼叫 DELETE /api/v1/subjects/{subject_id}")
def step_delete_subject(context, subject_id):
    """呼叫 DELETE /api/v1/subjects/{subject_id} 刪除自訂考科。"""
    email = context.memo.get("custom_owner_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # 取實際 subject_id：優先用 context.memo 中的第一個 custom_subject_ids
    actual_id = subject_id
    if "{subject_id}" in subject_id or subject_id == "{subject_id}":
        ids = context.memo.get("custom_subject_ids", [])
        actual_id = ids[0] if ids else subject_id

    response = context.api_client.delete(
        f"/api/v1/subjects/{actual_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
