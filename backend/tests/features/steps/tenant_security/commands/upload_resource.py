"""When 學生上傳一份 PDF 資源."""

from behave import when


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
        subject = Subject(id=uuid.uuid4(), name="一般科目", category_id=None)
        context.db_session.merge(subject)
        context.db_session.commit()
        subject_id = str(subject.id)
        context.ids["subject_default"] = subject_id

    response = context.api_client.post(
        "/api/v1/resources/upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": resource_name,
            "type": "pdf",
            "subject_id": subject_id,
        },
    )
    context.last_response = response
    context.memo["uploaded_resource_name"] = resource_name
    if response.status_code in (200, 201):
        data = response.json()
        context.ids["uploaded_resource"] = data.get("id", "")
