"""When 背景處理執行完成 — 同步跑 DocumentProcessingService.process_resource。"""

import uuid
from behave import when


@when('背景處理執行完成')
def step_impl(context):
    from app.services.document_processing_service import DocumentProcessingService
    resource_id = context.memo.get("last_resource_id")
    assert resource_id, "找不到 last_resource_id"
    service = DocumentProcessingService(context.db_session)
    try:
        service.process_resource(uuid.UUID(resource_id))
    except Exception:
        # 失敗路徑：service 內部已把 resource.status 設為 FAILED，允許 raise
        pass
    context.db_session.commit()
