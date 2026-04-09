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
        subject = Subject(id=uuid.uuid4(), name="一般科目", category_id=None)
        context.db_session.merge(subject)
        context.db_session.commit()
        subject_id = str(subject.id)
        context.ids["subject_default"] = subject_id

    response = context.api_client.post(
        "/api/v1/resources/upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "YouTube Video",
            "type": "youtube",
            "youtube_url": url,
            "subject_id": subject_id,
        },
    )
    context.last_response = response
    context.memo["submitted_url"] = url
