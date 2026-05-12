"""When step actions — Feature 46 enqueue failure BDD."""

import uuid

from behave import when


@when('呼叫 enqueue_process_resource(resource_id, user_id, tenant_id)')
def step_call_enqueue(context):
    from app.services.cloud_tasks_service import (
        EnqueueFailedError,
        enqueue_process_resource,
    )
    rid = context.memo.get("last_resource_id") or str(uuid.uuid4())
    uid = str(context.memo.get("last_user_id") or uuid.uuid4())
    try:
        enqueue_process_resource(resource_id=rid, user_id=uid, tenant_id=uid)
        context.memo["enqueue_raised"] = None
    except EnqueueFailedError as e:
        context.memo["enqueue_raised"] = e
    except Exception as e:
        # 任何其他 exception 也記下供斷言
        context.memo["enqueue_raised_other"] = e
        context.memo["enqueue_raised"] = None


@when('用戶 alice 觸發排程（catch EnqueueFailedError 流程）')
def step_simulate_endpoint_catch(context):
    """模擬 API endpoint 流程：呼叫 enqueue → catch EnqueueFailedError →
    _mark_resource_failed。"""
    from app.api.resource import _mark_resource_failed
    from app.services.cloud_tasks_service import (
        EnqueueFailedError,
        enqueue_process_resource,
    )

    db = context.db_session
    rid = context.memo["last_resource_id"]
    uid = str(context.memo["last_user_id"])
    try:
        enqueue_process_resource(resource_id=rid, user_id=uid, tenant_id=uid)
        context.memo["endpoint_status"] = 202
    except EnqueueFailedError as exc:
        _mark_resource_failed(db, rid, str(exc))
        db.commit()
        context.memo["endpoint_status"] = 503
        context.memo["endpoint_error"] = str(exc)
