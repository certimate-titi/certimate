"""When 用戶提交 URL 作為 YouTube 資源（SSRF 防護測試）."""

from behave import when


@when('用戶提交 URL "{url}" 作為 YouTube 資源')
def step_impl(context, url):
    """提交 YouTube URL，觸發 SSRF 防護驗證。"""
    token = context.memo.get("current_token")
    # 取得 subject_id
    subject_id = None
    for k, v in context.ids.items():
        if k.startswith("subject_"):
            subject_id = v
            break
    if not subject_id:
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
        "/api/v1/resources/youtube",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "youtube_url": url,
            "subject_id": subject_id,
        },
    )
    context.last_response = response
    context.memo["submitted_url"] = url
