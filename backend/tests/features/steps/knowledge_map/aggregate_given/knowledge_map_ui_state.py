"""Given 知識心智圖 UI 前置狀態 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 已進入知識心智圖頁面')
def step_impl_user_in_knowledge_map(context, email):
    """記錄使用者已進入知識心智圖頁面（UI 前置狀態）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if user:
        token = context.jwt_helper.create_token(str(user.id))
        context.memo["km_user_email"] = email
        context.memo["km_token"] = token


@given('使用者 "{email}" 在資源面板選中一份文件')
def step_impl_resource_selected(context, email):
    """記錄使用者在資源面板選中文件（UI 前置狀態）。"""
    import uuid
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["km_user_email"] = email
    context.memo["km_token"] = token

    from app.models.resource import Resource, ResourceType, ResourceStatus
    resource = context.db_session.query(Resource).filter(
        Resource.user_id == user.id
    ).first()
    if not resource:
        # 確保該使用者擁有可刪除的資源
        subject_id = None
        sid_key = "subject_AWS SAA"
        if sid_key in context.ids:
            subject_id = uuid.UUID(context.ids[sid_key])
        resource = Resource(
            user_id=user.id, subject_id=subject_id,
            name="待刪除文件.pdf", type=ResourceType.PDF,
            status=ResourceStatus.COMPLETED,
        )
        context.db_session.add(resource)
        context.db_session.commit()
    context.memo["selected_resource_id"] = str(resource.id)


@given('使用者 "{email}" 點擊了一個來源為 YouTube 的知識節點')
def step_impl_youtube_node_clicked(context, email):
    """記錄使用者點擊 YouTube 來源的知識節點（UI 前置狀態）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if user:
        token = context.jwt_helper.create_token(str(user.id))
        context.memo["km_user_email"] = email
        context.memo["km_token"] = token


@given('該節點的影片時間戳為 "{timestamp}"')
def step_impl_video_timestamp(context, timestamp):
    """記錄知識節點的影片時間戳（UI 前置狀態）。"""
    context.memo["video_timestamp"] = timestamp


@given('使用者 "{email}" 已點擊一個知識節點進入 AI 教練面板')
def step_impl_user_in_ai_coach_panel(context, email):
    """記錄使用者已點擊知識節點進入 AI 教練面板（UI 前置狀態）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if user:
        token = context.jwt_helper.create_token(str(user.id))
        context.memo["km_user_email"] = email
        context.memo["km_token"] = token
        context.memo["ai_coach_panel_open"] = True
