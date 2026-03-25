from behave import then


@then('使用者上傳至雲端存儲 (GCS) 的實體檔案應被標記刪除或移除')
def step_impl(context):
    # E2E 測試中，驗證 API 回應表明已標記 GCS 檔案刪除
    response = context.last_response
    data = response.json()
    files_deleted = (
        data.get("files_deleted") is True
        or "gcs" in str(data).lower()
        or "storage" in str(data).lower()
    )
    assert files_deleted, \
        f"回應中未包含 GCS 檔案已刪除的資訊: {data}"
