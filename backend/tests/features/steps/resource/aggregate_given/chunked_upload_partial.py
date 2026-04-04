from behave import given


@given('已成功上傳前 {uploaded:d} 片')
def step_impl(context, uploaded):
    context.memo["uploaded_chunks"] = uploaded

    # Update in-memory store
    upload_id = context.memo.get("upload_id")
    if upload_id:
        from app.services.chunked_upload_service import _uploads
        if upload_id in _uploads:
            _uploads[upload_id]["uploaded_chunks"] = set(range(uploaded))
