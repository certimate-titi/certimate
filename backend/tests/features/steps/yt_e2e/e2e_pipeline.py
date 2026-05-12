"""F47 E2E pipeline steps — tasks/process-resource 端到端驗證。

memory feedback_e2e_upload_parse_bdd.md：動到 resource pipeline 的 PR 必補此類 e2e BDD。

設計原則：
  - tasks/process-resource endpoint 走真實 router（不 mock）
  - document_processing_service.process_resource mock 為寫入 ResourceChunk + 回傳 OK
  - resource_parse_service 的 create_parse_job / run_parse_job mock 為建真實 DB row
  - 驗證 early-skip 邏輯不阻斷 YouTube resource（type-aware skip）
"""

from __future__ import annotations

import os
import uuid
from unittest.mock import patch, MagicMock

from behave import given, when, then

from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope
from app.models.resource_chunk import ResourceChunk
from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob


PUBLIC_B2C_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000b2cb2c")


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------

@given('環境變數 BACKGROUND_PROCESSOR 設為 inline')
def step_set_background_processor_inline(context):
    """強制設定 inline 模式，跳過 OIDC 驗證。"""
    os.environ["BACKGROUND_PROCESSOR"] = "inline"


@given('使用者 "{email}" 有一筆 YouTube 資源（無 gcs_path）')
def step_create_youtube_resource_no_gcs(context, email):
    """在 DB 建立 youtube type 資源，gcs_path=None，youtube_url 有值。"""
    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"

    subject_uuid_str = context.ids.get("subject_1")
    assert subject_uuid_str is not None, "找不到 subject_1，請先執行 Background"
    subject_uuid = uuid.UUID(subject_uuid_str)

    resource = Resource(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        subject_id=subject_uuid,
        name="Test YT Video",
        type=ResourceType.YOUTUBE.value,
        scope=ResourceScope.PERSONAL.value,
        status=ResourceStatus.PENDING.value,
        gcs_path=None,  # 沒有 gcs_path，這是 YT 的正常狀態
        youtube_url="https://www.youtube.com/watch?v=test_e2e_001",
        tenant_id=PUBLIC_B2C_TENANT_ID,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    # 存到 context 供後續 When/Then 使用
    context.memo["yt_e2e_resource_id"] = str(resource.id)
    context.memo["yt_e2e_user_id"] = user_id


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

def _call_process_resource(context, mock_doc_processing_ok: bool, mock_parse_job_success: bool):
    """共用 helper：呼叫 tasks/process-resource，注入 mock。

    - document_processing_service.DocumentProcessingService.process_resource：
      控制是否寫 chunk + 回傳 OK
    - resource_parse_service.create_parse_job / run_parse_job：
      建真實 DB row（ParseJobStatus.SUCCESS）
    """
    resource_id = context.memo.get("yt_e2e_resource_id")
    user_id = context.memo.get("yt_e2e_user_id")
    assert resource_id, "yt_e2e_resource_id 未設定"
    assert user_id, "yt_e2e_user_id 未設定"

    db = context.db_session

    def fake_process_resource(self_svc, rid):
        """Fake DocumentProcessingService.process_resource：寫入 1 個 ResourceChunk。

        使用 self_svc.db（request-scoped session）寫入 chunk 並明確 commit，
        讓後續 context.db_session 可透過同一 connection pool 讀到。
        """
        if mock_doc_processing_ok:
            chunk = ResourceChunk(
                id=uuid.uuid4(),
                resource_id=rid,
                chunk_index=0,
                content="Test chunk content from YT E2E",
                token_count=10,
                tenant_id=PUBLIC_B2C_TENANT_ID,
            )
            self_svc.db.add(chunk)
            self_svc.db.commit()
            return {"ok": True, "chunks_created": 1}
        return {"error": True, "message": "fake doc processing failed"}

    def fake_run_parse_job(inner_db, job_id):
        """Fake run_parse_job：把 DB 中的 job 狀態設為 SUCCESS，回傳 ParseOutcome。"""
        from app.services.resource_parse_service import ParseOutcome
        job = inner_db.get(ResourceParseJob, job_id)
        if job:
            job.status = ParseJobStatus.SUCCESS.value
            inner_db.flush()
        return ParseOutcome(
            job_id=job_id,
            status=ParseJobStatus.SUCCESS,
            questions_created=0,
            candidates_created=0,
            scaffolds_created=0,
            pages_rendered=0,
        )

    os.environ["BACKGROUND_PROCESSOR"] = "inline"

    # tasks endpoint 不走 async，直接 POST
    with patch(
        "app.services.document_processing_service.DocumentProcessingService.process_resource",
        fake_process_resource,
    ), patch(
        "app.services.resource_parse_service.run_parse_job",
        fake_run_parse_job,
    ):
        response = context.api_client.post(
            "/api/v1/tasks/process-resource",
            json={
                "resource_id": resource_id,
                "user_id": user_id,
                "tenant_id": str(PUBLIC_B2C_TENANT_ID),
            },
        )

    context.last_response = response


@when('系統觸發 tasks/process-resource（mock document_processing + parse_job）')
def step_trigger_process_resource_basic(context):
    """觸發 process-resource，只驗 early-skip 修正（不需 chunk/parse 副作用）。"""
    _call_process_resource(context, mock_doc_processing_ok=True, mock_parse_job_success=True)


@when('系統觸發 tasks/process-resource（mock document_processing 產生 chunk + mock parse_job 成功）')
def step_trigger_process_resource_full(context):
    """觸發 process-resource，驗 chunk + parse_job 都寫入 DB。"""
    _call_process_resource(context, mock_doc_processing_ok=True, mock_parse_job_success=True)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then('tasks endpoint 回應 status 不為 skipped')
def step_assert_status_not_skipped(context):
    """確認 early-skip 已修正：YT resource 不再回傳 status=skipped。"""
    resp = context.last_response
    assert resp is not None, "無 last_response"
    assert resp.status_code != 422, f"預期非 422，實際：{resp.status_code} {resp.text}"
    data = resp.json()
    status = data.get("status")
    assert status != "skipped", (
        f"YT resource 不應被 early-skip，但回應 status=skipped。"
        f"這代表 tasks.py line 290 gcs_path 檢查沒有豁免 type=youtube。"
        f"完整回應：{data}"
    )


@then('tasks endpoint 回應 ok 為 true')
def step_assert_ok_true(context):
    """確認回應 ok=true。"""
    data = context.last_response.json()
    assert data.get("ok") is True, f"預期 ok=true，實際：{data}"


@then('resource_chunks 表對該資源至少有 1 筆記錄')
def step_assert_resource_chunks_written(context):
    """對 DB 表直接斷言（memory feedback_bdd_must_assert_downstream_visibility.md）。"""
    db = context.db_session
    db.expire_all()
    resource_id = uuid.UUID(context.memo["yt_e2e_resource_id"])
    count = (
        db.query(ResourceChunk)
        .filter(ResourceChunk.resource_id == resource_id)
        .count()
    )
    assert count >= 1, (
        f"resource_chunks 表對 resource_id={resource_id} 應有 >= 1 筆，"
        f"實際：{count} 筆。這代表 YT pipeline chunk 寫入失敗。"
    )


@then('resource_parse_jobs 表對該資源至少有 1 筆 SUCCESS 記錄')
def step_assert_parse_job_success(context):
    """對 DB 表直接斷言 parse_job。"""
    db = context.db_session
    db.expire_all()
    resource_id = uuid.UUID(context.memo["yt_e2e_resource_id"])
    count = (
        db.query(ResourceParseJob)
        .filter(
            ResourceParseJob.resource_id == resource_id,
            ResourceParseJob.status == ParseJobStatus.SUCCESS.value,
        )
        .count()
    )
    assert count >= 1, (
        f"resource_parse_jobs 表對 resource_id={resource_id} 應有 >= 1 筆 SUCCESS，"
        f"實際：{count} 筆。"
    )
