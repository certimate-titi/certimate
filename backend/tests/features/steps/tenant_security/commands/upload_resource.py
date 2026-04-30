"""When 學生/散客上傳一份 PDF 資源."""

from behave import when


@when('散客上傳一份 PDF 資源「{resource_name}」')
def step_b2c_upload(context, resource_name):
    """散客版本：與學生上傳相同邏輯，使用 B2C 散客 token。"""
    # 直接複用相同邏輯
    step_impl(context, resource_name)


@when('學生上傳一份 PDF 資源「{resource_name}」')
def step_impl(context, resource_name):
    """透過 API 上傳 PDF 資源，帶入 tenant_id JWT。"""
    token = context.memo.get("current_token")
    # 取得第一個 subject（需要 subject_id）
    subject_id = None
    for k, v in context.ids.items():
        if k.startswith("subject_"):
            subject_id = v
            break

    if not subject_id:
        # 先建立一個 subject（透過 API 或直接 DB）
        import uuid
        from app.models.subject import Subject
        from app.models.subject import SubjectCategory
        category = context.db_session.query(SubjectCategory).first()
        if category is None:
            category = SubjectCategory(name="一般分類")
            context.db_session.add(category)
            context.db_session.commit()
            context.db_session.refresh(category)
        subject = Subject(id=uuid.uuid4(), name="一般科目", category_id=category.id)
        context.db_session.merge(subject)
        context.db_session.commit()
        subject_id = str(subject.id)
        context.ids["subject_default"] = subject_id

    response = context.api_client.post(
        "/api/v1/resources/upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": resource_name,
            "type": "pdf",
            "subject_id": subject_id,
            "file_size_mb": 1.0,
        },
    )
    context.last_response = response
    context.memo["uploaded_resource_name"] = resource_name
    if response.status_code in (200, 201):
        data = response.json()
        resource_id = data.get("id", "")
        context.ids["uploaded_resource"] = resource_id

        # BDD 測試中手動建立 chunk，驗證 tenant_id 設定機制
        # （正式環境由 background pipeline 自動建立）
        if resource_id:
            import uuid
            from app.models.resource_chunk import ResourceChunk
            from app.models.resource import Resource
            resource = context.db_session.query(Resource).filter(
                Resource.id == uuid.UUID(resource_id)
            ).first()
            if resource and resource.tenant_id:
                chunk = ResourceChunk(
                    id=uuid.uuid4(),
                    resource_id=resource.id,
                    chunk_index=0,
                    content="Test chunk for tenant_id verification",
                    token_count=10,
                    tenant_id=resource.tenant_id,
                )
                context.db_session.add(chunk)
                context.db_session.commit()
