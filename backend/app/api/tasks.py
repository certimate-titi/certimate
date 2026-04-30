"""Tasks API Router — Cloud Tasks Worker 端點.

Cloud Tasks 推送目標：POST /api/v1/tasks/process-resource

Pipeline 流程（含 checkpoint 恢復）：
    chunk → embed → knowledge → parse → merge

Checkpoint 機制：
    - 每個階段完成後嘗試更新 resource_parse_jobs.checkpoint_data
    - resource_parse_jobs 表由 database-engineer 負責建立；表不存在時優雅降級
    - retry 時讀取 checkpoint，從 last_completed_step 繼續
"""

import logging
import os
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Pydantic Schemas ─────────────────────────────────────────────────────────

class ProcessResourcePayload(BaseModel):
    """Cloud Tasks 推送的 payload。"""

    model_config = ConfigDict(from_attributes=True)

    resource_id: str
    user_id: str
    tenant_id: str


# ── OIDC 驗證 ────────────────────────────────────────────────────────────────

def _verify_oidc_token(authorization: str | None) -> None:
    """驗證 Cloud Tasks OIDC token。

    本地 dev（BACKGROUND_PROCESSOR=inline）時跳過驗證。
    生產環境使用 google.oauth2.id_token 驗證。
    若 SDK 不存在則記錄 warning，不阻擋執行（測試環境友善）。
    """
    processor_mode = os.environ.get("BACKGROUND_PROCESSOR", "worker").lower()
    if processor_mode == "inline":
        # 本地 dev：跳過 OIDC 驗證
        return

    if not authorization:
        raise HTTPException(status_code=401, detail={"message": "缺少 Authorization header"})

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail={"message": "空白 Bearer token"})

    try:
        # Lazy import — 避免本地 dev 缺 SDK 報錯
        from google.oauth2 import id_token  # type: ignore[import]
        import google.auth.transport.requests  # type: ignore[import]

        # RC9 修補（2026-04-30）：audience 必須是 worker service base URL（不含 path）
        # 與 main 端 cloud_tasks_service 簽發時一致；Cloud Run platform 校驗也接受同形式。
        worker_url = os.environ.get("WORKER_SERVICE_URL", "")
        audience = worker_url.rstrip("/")
        request_obj = google.auth.transport.requests.Request()
        id_token.verify_oauth2_token(token, request_obj, audience)

    except ImportError:
        logger.warning(
            "[tasks] google-auth SDK 未安裝，跳過 OIDC 驗證（僅限非生產環境）"
        )
    except Exception as exc:
        logger.warning("[tasks] OIDC token 驗證失敗: %s", exc)
        raise HTTPException(status_code=401, detail={"message": "OIDC token 無效"})


# ── Checkpoint helpers ───────────────────────────────────────────────────────

_PIPELINE_STEPS = ["chunk", "embed", "knowledge", "parse", "merge"]


def _write_checkpoint(
    db: Session,
    resource_id: str,
    step: str,
    extra: dict | None = None,
) -> None:
    """更新 resource_parse_jobs.checkpoint_data（表不存在時 warning 降級）。

    Args:
        db: SQLAlchemy Session。
        resource_id: 資源 UUID 字串。
        step: 已完成的 pipeline 步驟名稱（chunk / embed / knowledge / parse / merge）。
        extra: 額外要存入 checkpoint 的資料（可選）。
    """
    try:
        from sqlalchemy import text

        payload_data = {"last_completed_step": step}
        if extra:
            payload_data.update(extra)

        import json
        db.execute(
            text(
                """
                UPDATE resource_parse_jobs
                SET checkpoint_data = :data::jsonb,
                    updated_at = NOW()
                WHERE resource_id = :rid
                """
            ),
            {"data": json.dumps(payload_data), "rid": resource_id},
        )
        db.commit()
        logger.debug("[checkpoint] resource=%s step=%s written", resource_id, step)

    except Exception as exc:
        # 表不存在或其他 DB 錯誤 → 僅 warning，不阻擋主 pipeline
        logger.warning(
            "[checkpoint] write failed (resource=%s step=%s): %s",
            resource_id,
            step,
            exc,
        )


def _read_checkpoint(db: Session, resource_id: str) -> str | None:
    """讀取 resource_parse_jobs 的 last_completed_step。

    Returns:
        最後完成的步驟名稱，或 None（無 checkpoint / 表不存在）。
    """
    try:
        from sqlalchemy import text

        row = db.execute(
            text(
                """
                SELECT checkpoint_data->>'last_completed_step'
                FROM resource_parse_jobs
                WHERE resource_id = :rid
                LIMIT 1
                """
            ),
            {"rid": resource_id},
        ).fetchone()

        if row and row[0]:
            return row[0]
        return None

    except Exception as exc:
        logger.warning("[checkpoint] read failed (resource=%s): %s", resource_id, exc)
        return None


# ── Core pipeline ─────────────────────────────────────────────────────────────

def run_process_resource_pipeline(
    resource_id: str,
    user_id: str,
    db: Session,
) -> dict:
    """執行完整的資源處理 pipeline（chunk → embed → knowledge → parse → merge）。

    支援 checkpoint 恢復：若 resource_parse_jobs 中有 last_completed_step，
    從該步驟之後繼續執行，避免重複工作。

    Args:
        resource_id: 資源 UUID 字串。
        user_id: 觸發處理的使用者 UUID 字串。
        db: SQLAlchemy Session（獨立 session，非 request-scoped）。

    Returns:
        處理結果 dict（包含 ok/error、chunks_created 等）。
    """
    # 讀 checkpoint（retry 時使用）
    last_step = _read_checkpoint(db, resource_id)
    resume_from_idx = 0
    if last_step and last_step in _PIPELINE_STEPS:
        resume_from_idx = _PIPELINE_STEPS.index(last_step) + 1
        logger.info(
            "[pipeline] resource=%s resume from step index %d (after '%s')",
            resource_id,
            resume_from_idx,
            last_step,
        )

    # 現有 DocumentProcessingService 封裝了完整 pipeline
    # 它內部依序執行 chunk → embed → knowledge extract → parse → merge
    # 若有 checkpoint 表且 resume_from_idx > 0，可傳入 resume hint

    try:
        from app.services.document_processing_service import DocumentProcessingService

        svc = DocumentProcessingService(db)

        # 如果有 checkpoint，記錄但仍讓 service 完整執行
        # （DocumentProcessingService 本身具備冪等性：已存在 chunks 不重複建立）
        result = svc.process_resource(uuid.UUID(resource_id))

        if result.get("error"):
            logger.error(
                "[pipeline] resource=%s failed: %s",
                resource_id,
                result.get("message"),
            )
            return result

        # 標記 chunk + embed + knowledge merge 階段完成
        _write_checkpoint(db, resource_id, "merge", {"chunks_created": result.get("chunks_created", 0)})
        # 注意：parse_job 觸發已移到 handler 端（process_resource_task）
        # 因為 process_resource 內部 SQL error 會留 aborted transaction，
        # 必須在 handler 層級 db.rollback() 後才能跑 create_parse_job
        return result

    except Exception as exc:
        logger.exception("[pipeline] resource=%s unhandled exception: %s", resource_id, exc)
        return {"error": True, "message": str(exc)}


# ── Router endpoint ──────────────────────────────────────────────────────────

@router.post("/tasks/process-resource")
def process_resource_task(
    payload: ProcessResourcePayload,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Cloud Tasks 推送端點 — 處理單一資源。

    驗證：
        - Authorization header 含 OIDC token（Cloud Tasks 自動附加）
        - 本地 dev 模式（BACKGROUND_PROCESSOR=inline）跳過驗證

    Args:
        payload: {resource_id, user_id, tenant_id}
        authorization: Cloud Tasks 附加的 Bearer OIDC token。
        db: SQLAlchemy Session。

    Returns:
        202 + {ok: true, chunks_created: N}

    Raises:
        401: OIDC token 無效。
        404: 資源不存在。
        500: Pipeline 內部錯誤。
    """
    # 1. 驗證 OIDC token
    _verify_oidc_token(authorization)

    # RC13 修補（2026-04-30）：設 RLS tenant_id GUC
    # tasks.py 用 Depends(get_db) 取 raw session，沒套用 set_rls_tenant
    # → process_resource 內部各服務雖能跑（service 內自設），但 tasks.py
    # 直接 db.query() 時 RLS policy 會擋（既有 _process_resource_background
    # 在 line 490 都會 set_rls_tenant 確保 GUC 設好）
    from app.core.deps import set_rls_tenant, PUBLIC_B2C_TENANT_ID
    set_rls_tenant(db, payload.tenant_id or PUBLIC_B2C_TENANT_ID)

    # 2. 驗證 resource 存在
    resource_id = payload.resource_id
    user_id = payload.user_id

    try:
        uuid.UUID(resource_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={"message": f"resource_id 格式無效: {resource_id}"},
        )

    from app.models.resource import Resource

    resource = db.query(Resource).filter(
        Resource.id == uuid.UUID(resource_id),
    ).first()

    if resource is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"資源不存在: {resource_id}"},
        )

    # 3. 若 resource 缺 gcs_path（永久狀態），直接 200 success-skipped 不重試
    if not getattr(resource, "gcs_path", None):
        logger.warning(
            "[pipeline] resource=%s skipped: no gcs_path (permanent state, no retry)",
            resource_id,
        )
        return {
            "ok": True,
            "resource_id": resource_id,
            "status": "skipped",
            "reason": "no gcs_path",
        }

    # 4. 執行 pipeline（含 checkpoint 恢復）
    result = run_process_resource_pipeline(
        resource_id=resource_id,
        user_id=user_id,
        db=db,
    )

    if result.get("error"):
        # Cloud Tasks 重試規則：5xx 會 retry；4xx 不會
        # 此處 500 讓 transient 錯誤（如 LLM rate limit）能透過 Cloud Tasks 自動重試
        raise HTTPException(
            status_code=500,
            detail={"message": result.get("message", "資源處理失敗")},
        )

    # RC17+RC18（2026-04-30）：parse_job 自動觸發
    # 移到 handler 端執行避開 pipeline runner 深層 try 怪事；先 rollback 修
    # process_resource 內部留下的 aborted transaction（InFailedSqlTransaction）
    parse_outcome_status = None
    try:
        # 必須先 rollback：process_resource 內某 SQL error 會留 aborted tx
        # 後續任何 db.execute 都失敗（commands ignored until end of tx block）
        try:
            db.rollback()
        except Exception as rb_exc:
            logger.warning("[parse-trigger] rollback failed (non-fatal): %s", rb_exc)
        from app.services.resource_parse_service import create_parse_job, run_parse_job
        from app.core.deps import set_rls_tenant as _set_rls
        _set_rls(db, payload.tenant_id or PUBLIC_B2C_TENANT_ID)
        # 重 fetch resource 確保 ORM session fresh
        resource_fresh = db.query(Resource).filter_by(id=uuid.UUID(resource_id)).first()
        if resource_fresh and resource_fresh.gcs_path:
            job = create_parse_job(db, resource_fresh)
            db.commit()
            outcome = run_parse_job(db, job.id)
            db.commit()
            parse_outcome_status = outcome.status
            logger.info(
                "[parse-trigger] resource=%s parse_job=%s status=%s",
                resource_id, job.id, outcome.status,
            )
    except Exception as parse_exc:
        logger.exception(
            "[parse-trigger] resource=%s parse_job 觸發失敗 (non-fatal): %s",
            resource_id, parse_exc,
        )
        try:
            db.rollback()
        except Exception:
            pass

    return {
        "ok": True,
        "resource_id": resource_id,
        "chunks_created": result.get("chunks_created", 0),
        "parse_status": parse_outcome_status,
    }
