"""平台管理後台 API。"""

import os
import sys
import subprocess
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin")


# ── Version Info (public, no auth) ──────────────────────────────────────────

def _get_git_commit() -> str:
    """Get short git commit hash, fallback to 'dev'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "dev"
    except Exception:
        return "dev"


_CACHED_COMMIT = _get_git_commit()


# Container startup time — best-effort fallback when DEPLOYED_AT env var unset
_STARTUP_TIME = datetime.now(timezone.utc).isoformat(timespec="seconds")


@router.get("/version")
def get_version(db: Session = Depends(get_db)):
    """公開版本資訊端點（不需認證）。

    Real-time values:
    - alembic_head: queried from alembic_version table (never stale)
    - backend_commit: BUILD_COMMIT env var (set by Cloud Build), fallback to git
    - deployed_at: DEPLOYED_AT env var (set by Cloud Build), fallback to
      container startup time which is a reasonable proxy
    """
    from sqlalchemy import text as _sql_text

    database_url = os.environ.get("DATABASE_URL", "")
    environment = "production" if "cloudsql" in database_url else "development"

    # Real alembic head from DB
    try:
        alembic_head = db.execute(
            _sql_text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar() or "unknown"
    except Exception:
        alembic_head = "unknown"

    # Commit: prefer env var (Cloud Build sets BUILD_COMMIT=$SHORT_SHA),
    # fall back to git (works in dev), then "dev"
    commit = (
        os.environ.get("BUILD_COMMIT")
        or _CACHED_COMMIT
        or "dev"
    )

    # Deployed at: env var (Cloud Build sets DEPLOYED_AT=$BUILD_TIMESTAMP)
    # or container startup time (reasonable proxy — Cloud Run restarts on
    # each deploy so startup ≈ deploy).
    deployed_at = os.environ.get("DEPLOYED_AT") or _STARTUP_TIME

    return {
        "backend_version": os.environ.get("BACKEND_VERSION", "0.3.1"),
        "backend_commit": commit,
        "api_prefix": "/api/v1",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "alembic_head": alembic_head,
        "deployed_at": deployed_at,
        "environment": environment,
    }


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


# ── API Key Health & Management（Spec 12c §API Keys）──────────────────────────

@router.get("/api-keys/status")
def api_keys_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出 4 把 LLM API key 的健康狀態（last_4 / healthy / last_check_at）。"""
    import uuid as _uuid
    from app.models.user import User, UserRole
    user = db.query(User).filter_by(id=_uuid.UUID(user_id)).first()
    if not user or user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail={"message": "需要管理員權限"})
    from app.services.api_key_health_service import ApiKeyHealthService
    return ApiKeyHealthService(db).get_all_statuses()


@router.post("/api-keys/{provider}/test")
def api_key_test(
    provider: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """對 provider 發送 1-token ping 驗證 key 有效（cost ~$0.000001）。"""
    import uuid as _uuid
    from app.models.user import User, UserRole
    from app.services.api_key_health_service import ApiKeyHealthService, PROVIDERS
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail={"message": f"不支援的 provider: {provider}"})
    user = db.query(User).filter_by(id=_uuid.UUID(user_id)).first()
    if not user or user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail={"message": "需要管理員權限"})
    return ApiKeyHealthService(db).test_key(provider)  # type: ignore[arg-type]


class _UpdateApiKeyRequest(BaseModel):
    """重設 API key 的 request body。"""
    api_key: str


@router.put("/api-keys/{provider}")
def api_key_update(
    provider: str,
    body: _UpdateApiKeyRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """重設 API key（寫入 Secret Manager；本地僅提示）。

    Spec Q5: 僅 SUPER_ADMIN 可呼叫。
    """
    import uuid as _uuid
    from app.models.user import User, UserRole
    from app.services.api_key_health_service import ApiKeyHealthService, PROVIDERS
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail={"message": f"不支援的 provider: {provider}"})
    user = db.query(User).filter_by(id=_uuid.UUID(user_id)).first()
    if not user or user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})
    result = ApiKeyHealthService(db).update_key(user_id, provider, body.api_key)  # type: ignore[arg-type]
    if result.get("error"):
        raise HTTPException(status_code=result.get("status_code", 400), detail={"message": result["message"]})
    return result


# ── Resource Healing ─────────────────────────────────────────────────────────

@router.post("/resources/heal-orphans")
def heal_orphan_resources(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """掃描儲存體中遺失的資源檔案，標記為失敗以便用戶重新上傳。

    Spec 11 §「Admin healing endpoint 自動掃描並標記孤兒資源」
    僅 ADMIN / SUPER_ADMIN 可呼叫。
    """
    import uuid
    from app.models.user import User, UserRole
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    if not user or user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail={"message": "需要管理員權限"})
    from app.services.resource_library_service import ResourceLibraryService
    result = ResourceLibraryService(db).heal_orphan_resources()
    return result


@router.post("/resources/heal-stale-processing")
def heal_stale_processing(
    minutes: int = 30,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Bug #2 兜底（2026-04-29）— 掃 stale PROCESSING resource 強制標 FAILED。

    Cloud Run OOM SIGKILL 後 background task 無法 finally 兜底，resource 會永遠卡
    PROCESSING。Admin 可隨時呼叫此 endpoint 把超過 N 分鐘沒更新的 PROCESSING 標記為
    FAILED，讓用戶可看見錯誤訊息並重新上傳。

    Args:
        minutes: 多少分鐘沒更新算 stale，預設 30
    """
    import uuid
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import text
    from app.models.user import User, UserRole
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    if not user or user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail={"message": "需要管理員權限"})

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    res = db.execute(
        text(
            "UPDATE resources SET status='FAILED', "
            "error_message=COALESCE(error_message, :msg), "
            "updated_at=NOW() "
            "WHERE status='PROCESSING' AND updated_at < :cutoff "
            "RETURNING id, name"
        ),
        {"cutoff": cutoff, "msg": f"背景處理超時（{minutes} 分鐘無進度），admin 手動標記失敗"},
    )
    healed = [{"id": str(r[0]), "name": r[1]} for r in res]
    db.commit()
    return {"healed_count": len(healed), "healed": healed}


# ── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get dashboard。

    此 endpoint 對應 `get_dashboard` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.get_dashboard(user_id=user_id)
    return _handle_result(result)


def _build_daily_data_points(db, days: int, now):
    """Build N daily DAU/MAU data points."""
    from datetime import timedelta
    from sqlalchemy import func
    from app.models.user import User
    from app.models.exam import Exam

    total_users = db.query(func.count(User.id)).scalar() or 0
    data_points = []
    for offset in reversed(list(map(lambda x: x, range(days)))):
        day_start = (now - timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_exams = db.query(func.count(Exam.id)).filter(
            Exam.created_at >= day_start,
            Exam.created_at < day_end,
        ).scalar() or 0
        data_points.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "dau": day_exams,
            "mau": total_users,
        })
    return data_points


@router.get("/dashboard/charts")
def get_dashboard_charts(
    range: Optional[str] = None,
    type: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """管理後台圖表資料：用戶成長 + AI 成本分析。

    - ?range=90d → 回傳 90 筆每日 data_points（dau/mau）
    - ?type=ai_cost → 回傳按模型分列的 models 清單
    - 無參數 → 回傳月份 user_growth + ai_cost（舊格式，向下相容）
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func
    from app.models.user import User
    from app.models.exam import Exam, ExamStatus

    now = datetime.now(timezone.utc)

    # ── range=Nd → N 筆每日 DAU/MAU 資料點 ───────────────────────────────
    if range and range.endswith("d"):
        try:
            days = int(range[:-1])
        except ValueError:
            days = 30
        data_points = _build_daily_data_points(db, days, now)
        return {"data_points": data_points, "range": range}

    # ── type=ai_cost → 按模型分列的 Token 消耗量 ─────────────────────────
    if type == "ai_cost":
        total_exams = db.query(func.count(Exam.id)).filter(
            Exam.status.in_([ExamStatus.READY, ExamStatus.SUBMITTED]),
        ).scalar() or 0
        models = [
            {"model": "gemini-1.5-flash", "tokens": total_exams * 1500, "cost_usd": round(total_exams * 0.01, 4)},
            {"model": "claude-3.5-sonnet", "tokens": total_exams * 2000, "cost_usd": round(total_exams * 0.05, 4)},
            {"model": "gpt-4o", "tokens": 0, "cost_usd": 0},
        ]
        return {"models": models}

    # ── 預設：月份 user_growth + ai_cost ─────────────────
    user_growth = []
    for i in [5, 4, 3, 2, 1, 0]:
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_name = month_start.strftime("%m月")
        total_users = db.query(func.count(User.id)).filter(User.created_at <= month_start + timedelta(days=31)).scalar() or 0
        exams_in_month = db.query(func.count(Exam.id)).filter(
            Exam.created_at >= month_start,
            Exam.created_at < month_start + timedelta(days=31),
        ).scalar() or 0
        user_growth.append({
            "name": month_name,
            "dau": max(1, exams_in_month // 30),
            "mau": max(1, min(total_users, exams_in_month * 3)),
        })

    # AI cost — real data from ai_usage_ledger (Feature 33)
    from sqlalchemy import text as _text
    try:
        rows = db.execute(_text("""
            SELECT DATE_TRUNC('month', created_at) AS month,
                   provider,
                   SUM(cost_usd) AS total_cost
            FROM ai_usage_ledger
            WHERE created_at >= :start_date
            GROUP BY month, provider
            ORDER BY month
        """), {"start_date": now - timedelta(days=180)}).fetchall()
    except Exception:
        rows = []

    # Pivot: month → {gemini, claude, voyage, gpt4}
    by_month: dict = {}
    for month, provider, cost in rows:
        key = month.strftime("%m月") if month else ""
        if key not in by_month:
            by_month[key] = {"name": key, "gemini": 0.0, "claude": 0.0, "gpt4": 0.0, "voyage": 0.0}
        prov_key = "claude" if provider == "anthropic" else provider
        if prov_key in by_month[key]:
            by_month[key][prov_key] = round(float(cost or 0), 4)

    # Build last 6 months in order, fill zeros for empty months
    ai_cost = []
    for i in [5, 4, 3, 2, 1, 0]:
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_name = month_start.strftime("%m月")
        ai_cost.append(by_month.get(month_name, {
            "name": month_name, "gemini": 0.0, "claude": 0.0, "gpt4": 0.0, "voyage": 0.0,
        }))

    return {"user_growth": user_growth, "ai_cost": ai_cost}


@router.get("/dashboard/system-load")
def get_system_load(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """系統負載（真實值）。

    - cpu_percent: 當前 backend process CPU 使用率（psutil, 無 GCP API 費用）
    - db_connections_percent: PostgreSQL pg_stat_activity / max_connections
    - queue_depth_percent: 佇列深度（處理中資源 / 上限）— 取代原本的 Redis 假指標
    """
    from sqlalchemy import text as _text

    # CPU — psutil reads this process's CPU sample
    try:
        import psutil
        cpu_percent = int(psutil.cpu_percent(interval=0.1))
    except Exception:
        cpu_percent = 0

    # DB connections — SELECT count + max_connections
    try:
        rows = db.execute(_text("""
            SELECT
                (SELECT count(*) FROM pg_stat_activity WHERE state IS NOT NULL)::int AS active,
                current_setting('max_connections')::int AS maxc
        """)).first()
        active = rows[0] if rows else 0
        max_conn = rows[1] if rows and rows[1] else 100
        db_connections_percent = min(100, int(active * 100 / max_conn))
    except Exception:
        db_connections_percent = 0

    # Queue depth — processing resources vs 10 (small pool assumption)
    try:
        from app.models.resource import Resource, ResourceStatus
        from sqlalchemy import func
        processing = db.query(func.count(Resource.id)).filter(
            Resource.status == ResourceStatus.PROCESSING
        ).scalar() or 0
        queue_depth_percent = min(100, int(processing * 10))
    except Exception:
        queue_depth_percent = 0

    return {
        "cpu_percent": cpu_percent,
        "db_connections_percent": db_connections_percent,
        "queue_depth_percent": queue_depth_percent,
    }


@router.get("/dashboard/alerts")
def get_dashboard_alerts(
    worker_failure_rate: Optional[int] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """管理後台告警。

    - ?worker_failure_rate=N → 若 N > 5，觸發紅色 Worker 失敗率警報
    """
    from app.models.exam import Exam, ExamStatus
    from sqlalchemy import func

    failed_exams = db.query(func.count(Exam.id)).filter(Exam.status == ExamStatus.FAILED).scalar() or 0
    alerts = []
    if failed_exams > 0:
        alerts.append({"id": 1, "type": "warning", "level": "red", "message": f"{failed_exams} 個考試生成失敗", "content": f"{failed_exams} 個考試生成失敗", "time": "今天"})

    # Worker 失敗率超標警報
    if worker_failure_rate is not None and worker_failure_rate > 5:
        alerts.append({
            "id": 2,
            "type": "critical",
            "level": "red",
            "message": f"Worker 失敗率異常：{worker_failure_rate}%",
            "content": f"Worker 失敗率異常：{worker_failure_rate}%",
            "time": "剛剛",
        })

    # System alerts — real infrastructure checks
    system_alerts = []

    # Cloud SQL connection check
    try:
        from sqlalchemy import text as _text
        active_conn = db.execute(_text("SELECT count(*) FROM pg_stat_activity WHERE state IS NOT NULL")).scalar() or 0
        max_conn = int(db.execute(_text("SELECT current_setting('max_connections')")).scalar() or 25)
        if active_conn > max_conn * 0.8:
            system_alerts.append({
                "severity": "critical",
                "message": f"Cloud SQL 連線數 {active_conn}/{max_conn} (>{int(max_conn*0.8)})",
                "time": "即時",
            })
    except Exception:
        pass

    # Processing queue stuck check
    from app.models.resource import Resource, ResourceStatus
    stuck = db.query(func.count(Resource.id)).filter(
        Resource.status == ResourceStatus.PROCESSING,
    ).scalar() or 0
    if stuck > 5:
        system_alerts.append({
            "severity": "warning",
            "message": f"{stuck} 個資源處理卡住（PROCESSING 狀態）",
            "time": "即時",
        })

    return {"alerts": alerts, "system_alerts": system_alerts}


@router.get("/settings")
def get_system_settings(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get system settings。

    此 endpoint 對應 `get_system_settings` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.get_system_settings(user_id=user_id)
    return _handle_result(result)


# ── User Management ──────────────────────────────────────────────────────────


class CreateUserRequest(BaseModel):
    email: str
    password: str


@router.post("/users")
def create_user(
    body: CreateUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """create user。

    此 endpoint 對應 `create_user` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.create_user(
        actor_id=user_id,
        email=body.email,
        password=body.password,
    )
    return _handle_result(result)


@router.get("/users")
def search_users(
    keyword: Optional[str] = None,
    plan: Optional[str] = None,
    role: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """search users。

    此 endpoint 對應 `search_users` 操作。

    Args:
        keyword: 參數。
        plan: 參數。
        role: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.search_users(actor_id=user_id, keyword=keyword, plan=plan, role=role)
    return _handle_result(result)


@router.get("/users/export")
def export_users_csv(
    plan: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """export users csv。

    此 endpoint 對應 `export_users_csv` 操作。

    Args:
        plan: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.export_users_csv(actor_id=user_id, plan=plan)
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    csv_content = result["csv_content"]
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@router.get("/users/{target_user_id}")
def get_user_detail(
    target_user_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """get user detail。

    此 endpoint 對應 `get_user_detail` 操作。

    Args:
        target_user_id: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.get_user_detail(actor_id=user_id, target_user_key=target_user_id)
    return _handle_result(result)


# ── Subscription Adjustment ──────────────────────────────────────────────────

class AdjustSubscriptionRequest(BaseModel):
    plan: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.post("/users/{target_user_id}/adjust-subscription")
def adjust_subscription(
    target_user_id: str,
    body: AdjustSubscriptionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """adjust subscription。

    此 endpoint 對應 `adjust_subscription` 操作。

    Args:
        target_user_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.adjust_subscription(
        actor_id=user_id,
        target_user_id=target_user_id,
        new_plan=body.plan,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return _handle_result(result)


# ── Suspend User ─────────────────────────────────────────────────────────────

class SuspendUserRequest(BaseModel):
    target_user_id: Optional[str] = None
    reason: Optional[str] = None


@router.post("/users/suspend")
def suspend_user(
    body: SuspendUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """suspend user。

    此 endpoint 對應 `suspend_user` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.suspend_user(
        actor_id=user_id,
        target_user_id=body.target_user_id,
        reason=body.reason,
    )
    return _handle_result(result)


# ── Activate User ────────────────────────────────────────────────────────────

class ActivateUserRequest(BaseModel):
    target_user_id: Optional[str] = None


@router.post("/users/activate")
def activate_user(
    body: ActivateUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """activate user。

    此 endpoint 對應 `activate_user` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.activate_user(
        actor_id=user_id,
        target_user_id=body.target_user_id,
    )
    return _handle_result(result)


# ── Adjust Role ─────────────────────────────────────────────────────────────

class AdjustRoleRequest(BaseModel):
    target_user_id: Optional[str] = None
    target_email: Optional[str] = None
    email: Optional[str] = None  # alias for target_email (used by some clients)
    role: str  # 'admin' or 'user'


@router.post("/users/adjust-role")
def adjust_role(
    body: AdjustRoleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """adjust role。

    此 endpoint 對應 `adjust_role` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    # Support both target_email and email fields
    target_email = body.target_email or body.email
    result = service.adjust_role(
        actor_id=user_id,
        target_user_id=body.target_user_id,
        target_email=target_email,
        new_role=body.role,
    )
    return _handle_result(result)


# ── Delete User ─────────────────────────────────────────────────────────────

class DeleteUserRequest(BaseModel):
    target_user_id: str
    confirm_name: str


@router.post("/users/delete")
def delete_user(
    body: DeleteUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """delete user。

    此 endpoint 對應 `delete_user` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.delete_user(
        actor_id=user_id,
        target_user_id=body.target_user_id,
        confirm_name=body.confirm_name,
    )
    return _handle_result(result)


# ── Notify User ──────────────────────────────────────────────────────────────

class NotifyUserRequest(BaseModel):
    message: str


@router.post("/users/{target_user_id}/notify")
def notify_user(
    target_user_id: str,
    body: NotifyUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """notify user。

    此 endpoint 對應 `notify_user` 操作。

    Args:
        target_user_id: 參數。
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = AdminService(db)
    result = service.notify_user(
        actor_id=user_id,
        target_user_id=target_user_id,
        message=body.message,
    )
    return _handle_result(result)


# ── Seed Subjects (for E2E test setup) ─────────────────────────────────────

class SeedSubjectsRequest(BaseModel):
    categories: list[dict]  # [{"name": "IT", "subjects": ["AWS SAA", "Azure AZ-900"]}]


# 預設考科清單（來自考古題爬蟲 catalog）
DEFAULT_EXAM_SUBJECTS = [
    {"name": "金融", "subjects": [
        "信託業業務人員", "證券商業務員", "人身保險業務員",
        "期貨商業務員", "防制洗錢與打擊資恐專業人員", "理財規劃人員",
        "CFA Level 1", "不動產經紀人", "地政士", "不動產估價師",
    ]},
    {"name": "IT", "subjects": [
        "AI 應用規劃師", "巨量資料分析師", "物聯網應用工程師",
        "區塊鏈智能合約開發者", "資訊安全工程師",
        "AWS SAA", "AWS SAP", "GCP ACE", "Azure AZ-900",
    ]},
    {"name": "語言", "subjects": ["TOEIC", "JLPT N1"]},
    {"name": "醫療", "subjects": ["護理師"]},
    {"name": "公務員", "subjects": ["普考"]},
]


@router.post("/sync-prompts", include_in_schema=False)
def sync_prompts():
    """從 GCS 同步 prompt templates 到 DB（CI 部署後觸發）。

    上傳 K-06 v2（含圖片內嵌）等更新到 prod DB。
    對應 .github/workflows/deploy-gcp.yml 部署後的 curl POST 步驟。
    """
    from app.scripts.sync_prompts_from_gcs import sync_and_seed_prompts
    try:
        result = sync_and_seed_prompts()
        return {"ok": True, "result": result}
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("sync_prompts failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"message": f"sync failed: {type(exc).__name__}: {exc}"},
        )


@router.post("/seed-subjects")
def seed_subjects(
    body: Optional[SeedSubjectsRequest] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """seed subjects。

    此 endpoint 對應 `seed_subjects` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    from app.models.subject import SubjectCategory, Subject

    categories_data = body.categories if body else DEFAULT_EXAM_SUBJECTS

    for cat_data in categories_data:
        cat_name = cat_data["name"]
        cat = db.query(SubjectCategory).filter_by(name=cat_name).first()
        if not cat:
            cat = SubjectCategory(name=cat_name)
            db.add(cat)
            db.flush()

        for subj_name in cat_data.get("subjects", []):
            existing = db.query(Subject).filter_by(name=subj_name, category_id=cat.id).first()
            if not existing:
                db.add(Subject(name=subj_name, category_id=cat.id))

    db.commit()
    return {"message": "Subjects seeded"}


@router.post("/seed-exam-codes")
def seed_exam_codes(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Set exam_subject_codes for all known subjects."""
    from app.models.subject import Subject

    CODES = {
        "AI 應用規劃師（初級）": [
            "IPA114:114_ai_fundamentals_4th",
            "IPA114:114_ai_application_4th",
        ],
        "AI 應用規劃師（中級）": [
            "IPA114:114_ai_mid_ml",
            "IPA114:114_ai_mid_bigdata",
            "IPA114:114_ai_mid_tech_planning",
        ],
        "證券商業務員": [
            "FIN114:securities_salesperson_session01_questions",
            "FIN114:securities_salesperson_session02_questions",
            "FIN114:senior_securities_session01_questions",
            "FIN114:senior_securities_session02_questions",
            "FIN114:securities_regulations_b_session01_questions",
            "FIN114:securities_regulations_b_session02_questions",
            "FIN114:internal_control_session01_questions",
            "FIN114:internal_control_session02_questions",
        ],
        "期貨商業務員": [
            "FIN114:futures_salesperson_session01_questions",
            "FIN114:futures_salesperson_session02_questions",
            "FIN114:futures_analyst_session01_questions",
            "FIN114:futures_analyst_session02_questions",
            "FIN114:futures_trust_fund_session01_questions",
            "FIN114:futures_trust_fund_session02_questions",
        ],
        "理財規劃人員": [
            "FIN114:investment_trust_session01_questions",
            "FIN114:investment_trust_session02_questions",
            "FIN114:investment_regulations_b_session01_questions",
            "FIN114:investment_regulations_b_session02_questions",
        ],
        "防制洗錢與打擊資恐專業人員": [
            "FIN114:aml_cft_session01_questions",
            "FIN114:aml_cft_session02_questions",
            "FIN114:sustainability_session01_questions",
            "FIN114:sustainability_session02_questions",
        ],
        "資訊安全工程師（初級）": [
            "IPA114:114_is_beginner_management",
            "IPA114:114_is_beginner_tech",
        ],
        "巨量資料分析師（初級）": [
            "IPA111:111_bda_beginner_subject1",
            "IPA111:111_bda_beginner_subject2",
            "IPA109:109_bda_beginner_sample_subject1",
            "IPA109:109_bda_beginner_sample_subject2",
        ],
        "不動產經紀人": [
            "REA111:111_land_law_q",
            "REA111:111_broker_regulations_q",
            "REA111:111_civil_law_q",
            "REA111:111_valuation_q",
            "REA112:112_land_law_q",
            "REA112:112_broker_regulations_q",
            "REA112:112_civil_law_q",
            "REA112:112_valuation_q",
        ],
    }
    updated = 0
    for name, codes in CODES.items():
        subject = db.query(Subject).filter_by(name=name).first()
        if subject:
            subject.exam_subject_codes = codes
            updated += 1
    db.commit()
    return {"message": f"Updated {updated} subjects with exam_subject_codes"}


@router.get("/debug-subject/{subject_id}")
def debug_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Debug: check subject data for extraction."""
    from app.models.subject import Subject
    from app.models.historical_exam import HistoricalExam
    from app.models.question import Question
    import uuid as uuid_mod
    from sqlalchemy import text, func

    sid = uuid_mod.UUID(subject_id)
    subject = db.query(Subject).filter_by(id=sid).first()
    if not subject:
        return {"error": f"Subject {subject_id} not found"}

    codes = subject.exam_subject_codes or []

    # Check historical_exams for each code
    code_results = []
    for code in codes:
        parts = code.split(':', 1)
        if len(parts) == 2:
            count = db.execute(text('''
                SELECT COUNT(*) FROM questions q
                JOIN historical_exams he ON q.historical_exam_id = he.id
                WHERE he.exam_code = :ec AND he.subject_code = :sc
            '''), {'ec': parts[0], 'sc': parts[1]}).scalar()
            code_results.append({"code": code, "questions": count})

    # Check by subject_name
    name_count = db.execute(text('''
        SELECT COUNT(*) FROM questions q
        JOIN historical_exams he ON q.historical_exam_id = he.id
        WHERE he.subject_name = :name
    '''), {'name': subject.name}).scalar()

    # Check all historical_exams
    he_count = db.query(func.count(HistoricalExam.id)).scalar()

    # Check knowledge nodes for this subject
    from app.models.knowledge_node import KnowledgeNode
    nodes = db.query(KnowledgeNode).filter_by(subject_id=sid).order_by(
        KnowledgeNode.depth, KnowledgeNode.sort_order
    ).all()
    node_data = [
        {"name": n.name, "depth": n.depth, "available_questions": n.available_questions or 0}
        for n in nodes
    ]

    # Count mapped historical questions (node_id points to this subject's nodes)
    node_ids = [n.id for n in nodes]
    mapped_count = 0
    if node_ids:
        placeholders = ', '.join(f':nid_{i}' for i in range(len(node_ids)))
        params = {f'nid_{i}': str(nid) for i, nid in enumerate(node_ids)}
        mapped_count = db.execute(text(f'''
            SELECT COUNT(*) FROM questions
            WHERE node_id IN ({placeholders}) AND historical_exam_id IS NOT NULL
        '''), params).scalar()

    return {
        "subject_id": subject_id,
        "name": subject.name,
        "exam_subject_codes": codes,
        "code_results": code_results,
        "name_match_count": name_count,
        "total_historical_exams": he_count,
        "knowledge_nodes": node_data,
        "total_nodes": len(nodes),
        "mapped_historical_questions": mapped_count,
    }


@router.post("/import-historical-questions")
def import_historical_questions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Import historical questions from JSON files inside the container."""
    from pathlib import Path
    from app.scripts.import_exam_questions import QuestionImporter

    json_dir = Path("/app/data/historical_questions")
    if not json_dir.exists():
        # Try local path
        json_dir = Path(__file__).parent.parent.parent / "data" / "historical_questions"
    if not json_dir.exists():
        raise HTTPException(status_code=404, detail={"message": f"JSON dir not found: {json_dir}"})

    importer = QuestionImporter(db, dry_run=False)

    imported = 0
    errors = []
    for json_file in sorted(json_dir.rglob("*.json")):
        if json_file.name.startswith("_") or "backup" in str(json_file):
            continue
        try:
            import json as json_mod
            data = json_mod.loads(json_file.read_text(encoding="utf-8"))
            meta = data.get("import_meta", {})
            if not meta.get("exam_code"):
                continue
            importer.import_from_json_file(json_file)
            imported += 1
        except Exception as e:
            errors.append(f"{json_file.name}: {str(e)}")

    return {
        "message": f"Imported {imported} files, {importer.imported_count} questions added, {importer.skipped_count} skipped",
        "errors": errors[:10] if errors else [],
    }


# ── GCS Sync + Import ──────────────────────────────────────────────────────

@router.post("/sync-questions")
def sync_questions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """從 GCS Bucket 同步考古題 JSON 並匯入資料庫。

    流程：GCS → /tmp/historical_questions/ → DB (upsert)
    """
    import logging
    log = logging.getLogger("admin.sync")

    try:
        from app.scripts.sync_from_gcs import sync_from_gcs, LOCAL_DIR
        from app.scripts.import_exam_questions import QuestionImporter

        # Step 1: Sync from GCS
        log.info("Starting GCS sync...")
        sync_result = sync_from_gcs()
        log.info(f"GCS sync result: {sync_result}")

        # Step 2: Import to DB
        log.info("Starting DB import...")
        importer = QuestionImporter(db, dry_run=False)
        importer.import_directory(LOCAL_DIR)

        import_result = {
            "imported": importer.imported_count,
            "skipped": importer.skipped_count,
            "errors": importer.error_count,
        }
        log.info(f"Import result: {import_result}")

        # Step 3: Seed exam_subject_codes
        from app.scripts.seed_exam_subject_codes import EXISTING_SUBJECT_CODES
        from app.models.subject import Subject

        seeded = 0
        for name, codes in EXISTING_SUBJECT_CODES.items():
            subject = db.query(Subject).filter_by(name=name).first()
            if subject and subject.exam_subject_codes != codes:
                subject.exam_subject_codes = codes
                seeded += 1
        if seeded > 0:
            db.commit()

        return {
            "message": "Sync complete",
            "sync": sync_result,
            "import": import_result,
            "seeded_codes": seeded,
        }

    except Exception as e:
        import traceback
        log.exception("Sync error: %s", e)
        raise HTTPException(status_code=500, detail={
            "message": f"Sync error: {str(e)}",
            "traceback": traceback.format_exc()[-500:],
        })


# ========== PRD-033 預設資源綁定（管理後台）==========

class BindDefaultResourceRequest(BaseModel):
    resource_id: str


@router.post("/subjects/{subject_id}/default-resources")
def bind_default_resource(
    subject_id: str,
    body: BindDefaultResourceRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """平台管理員：把 scope=platform 的資源綁定為某 subject 的預設資源。PRD-033 US-04。"""
    import uuid as _uuid
    from app.models.user import User
    from app.models.resource import Resource
    from app.models.subject_default_resource import SubjectDefaultResource

    try:
        user_uuid = _uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail={"message": "僅平台管理員可綁定預設資源"})
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user or (getattr(user, "role", "") not in ("admin", "super_admin")):
        raise HTTPException(status_code=403, detail={"message": "僅平台管理員可綁定預設資源"})

    resource = db.query(Resource).filter_by(id=body.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail={"message": "資源不存在"})
    resource_scope_val = resource.scope.value if hasattr(resource.scope, "value") else str(resource.scope)
    if resource_scope_val != "platform":
        raise HTTPException(status_code=400, detail={"message": "只能綁定 scope=platform 的資源"})

    existing = db.query(SubjectDefaultResource).filter_by(
        subject_id=_uuid.UUID(subject_id), resource_id=_uuid.UUID(body.resource_id)
    ).first()
    if existing:
        return {"ok": True, "already_bound": True}

    link = SubjectDefaultResource(
        subject_id=_uuid.UUID(subject_id),
        resource_id=_uuid.UUID(body.resource_id),
        added_by_user_id=_uuid.UUID(user_id),
    )
    db.add(link)
    db.commit()
    return {"ok": True, "subject_id": subject_id, "resource_id": body.resource_id}


@router.delete("/subjects/{subject_id}/default-resources/{resource_id}")
def unbind_default_resource(
    subject_id: str,
    resource_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """解除預設資源綁定。PRD-033 US-04。"""
    import uuid as _uuid
    from app.models.user import User
    from app.models.subject_default_resource import SubjectDefaultResource

    try:
        user_uuid = _uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail={"message": "僅平台管理員可操作"})
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user or (getattr(user, "role", "") not in ("admin", "super_admin")):
        raise HTTPException(status_code=403, detail={"message": "僅平台管理員可操作"})

    link = db.query(SubjectDefaultResource).filter_by(
        subject_id=_uuid.UUID(subject_id), resource_id=_uuid.UUID(resource_id)
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail={"message": "綁定不存在"})

    db.delete(link)
    db.commit()
    return {"ok": True}


# ── Sprint 8 T66：背景觸發 scaffold embedding backfill ─────────────────────

@router.post("/backfill-scaffold-embeddings")
def trigger_scaffold_backfill(
    background_tasks: BackgroundTasks,
    limit: int = 200,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """觸發 resource_scaffolds.embedding NULL row 補 voyage embedding（背景）。

    Sprint 8 T66：取代 CLI 手動跑，可由 super-admin 從後台一鍵觸發。
    backfill 在背景跑（FastAPI BackgroundTasks），即時回傳 NULL 數量。

    Args:
        limit: 本次最多處理筆數（避免燒爆 voyage 配額）。預設 200。

    僅 SUPER_ADMIN 可呼叫。
    """
    import uuid as _uuid
    from sqlalchemy import text
    from app.models.user import User, UserRole

    try:
        user_uuid = _uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user or user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})

    null_count = db.execute(
        text("SELECT COUNT(*) FROM resource_scaffolds WHERE embedding IS NULL")
    ).scalar_one()

    if null_count == 0:
        return {"queued": False, "null_count": 0, "message": "無需 backfill"}

    def _run_backfill(target_limit: int):
        """背景執行 backfill — 重用 CLI 腳本的 run() 函式。"""
        from app.scripts.backfill_scaffold_embeddings import run
        try:
            run(batch_size=64, limit=target_limit, dry_run=False)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("backfill_scaffold_embeddings failed")

    background_tasks.add_task(_run_backfill, limit)
    return {"queued": True, "null_count": null_count, "limit": limit}


# ── Sprint 10 T81：節點 embedding backfill + 觸發 scaffold relink ──────────

@router.post("/backfill-node-embeddings/{subject_id}")
def trigger_node_embedding_backfill(
    subject_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """為指定科目所有 embedding=NULL 的節點補 voyage embedding，並觸發
    scaffold_node_links re-link（讓 N:M 對應立即生效，不需等下次 unified
    extraction）。

    Sprint 10 T81 — 解決 PR #27 已部署但既有節點還沒 embedding 的問題。
    僅 SUPER_ADMIN 可呼叫。
    """
    import uuid as _uuid
    from sqlalchemy import text
    from app.models.user import User, UserRole

    try:
        user_uuid = _uuid.UUID(user_id)
        sid = _uuid.UUID(subject_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user or user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})

    null_count = db.execute(
        text("SELECT COUNT(*) FROM knowledge_nodes WHERE subject_id = :sid AND embedding IS NULL"),
        {"sid": str(sid)},
    ).scalar_one()

    def _run_backfill():
        from app.services.unified_knowledge_extraction_service import UnifiedKnowledgeExtractionService
        try:
            svc = UnifiedKnowledgeExtractionService(db)
            embedded = svc._embed_nodes_for_subject(sid)
            db.commit()
            relinked = svc._relink_subject_scaffolds(sid)
            db.commit()
            import logging
            logging.getLogger(__name__).info(
                "[T81 backfill] subject=%s embedded=%d relinked=%d", sid, embedded, relinked
            )
        except Exception:
            import logging
            logging.getLogger(__name__).exception("[T81 backfill] failed")
            db.rollback()

    if null_count == 0:
        # 仍跑 relink（即使 embedding 都已寫入，可能需要重建 link）
        background_tasks.add_task(_run_backfill)
        return {"queued": True, "null_count": 0, "note": "全部已有 embedding，僅執行 relink"}

    background_tasks.add_task(_run_backfill)
    return {"queued": True, "null_count": null_count, "note": "background task 啟動，預估 1-2 分鐘"}


# ── Sprint 10 T87：節點/鷹架 orphan 監控 ──────────────────────────────────

@router.get("/knowledge/orphan-stats")
def get_orphan_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """節點 ↔ 鷹架關聯品質監控（教育顧問驗收 KPI）。

    回傳：
      - 該科目節點總數 / orphan node（無任何 link 的節點）
      - 該科目 scaffold 總數 / orphan scaffold（無任何 link 的鷹架）
      - 平均 link similarity（0-1）
      - 每節點平均對應 scaffolds 數
    """
    import uuid as _uuid
    from sqlalchemy import text
    from app.models.user import User, UserRole

    try:
        user_uuid = _uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user or user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})

    rows = db.execute(text("""
        SELECT
          s.id AS subject_id, s.name,
          COUNT(DISTINCT kn.id) FILTER (WHERE kn.depth >= 2) AS depth2_nodes,
          COUNT(DISTINCT snl.node_id) FILTER (WHERE kn.depth >= 2) AS linked_nodes,
          COUNT(DISTINCT rs.id) AS scaffolds,
          COUNT(DISTINCT snl.scaffold_id) AS linked_scaffolds,
          AVG(snl.similarity)::float AS avg_sim,
          COUNT(snl.id)::float / NULLIF(COUNT(DISTINCT snl.node_id), 0) AS avg_links_per_node
        FROM subjects s
        LEFT JOIN knowledge_nodes kn ON kn.subject_id = s.id
        LEFT JOIN resources r ON r.subject_id = s.id
        LEFT JOIN resource_scaffolds rs ON rs.resource_id = r.id
        LEFT JOIN scaffold_node_links snl ON snl.node_id = kn.id
        GROUP BY s.id, s.name
        HAVING COUNT(DISTINCT kn.id) > 0 OR COUNT(DISTINCT rs.id) > 0
        ORDER BY s.name
    """)).fetchall()

    return {
        "subjects": [
            {
                "subject_id": str(r[0]),
                "name": r[1],
                "depth2_nodes": int(r[2] or 0),
                "linked_nodes": int(r[3] or 0),
                "orphan_nodes": int((r[2] or 0) - (r[3] or 0)),
                "orphan_node_pct": round(100 * (1 - (r[3] or 0) / (r[2] or 1)), 1) if r[2] else 0,
                "scaffolds": int(r[4] or 0),
                "linked_scaffolds": int(r[5] or 0),
                "orphan_scaffolds": int((r[4] or 0) - (r[5] or 0)),
                "orphan_scaffold_pct": round(100 * (1 - (r[5] or 0) / (r[4] or 1)), 1) if r[4] else 0,
                "avg_similarity": round(float(r[6]), 3) if r[6] else None,
                "avg_links_per_node": round(float(r[7]), 2) if r[7] else None,
            }
            for r in rows
        ]
    }


# ── 既有 fork subject 補抓 scaffolds（PR #37 前 fork 的修復 endpoint） ──────

@router.post("/repair-fork/{subject_id}")
def repair_fork_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """對 PR #37 前 fork 的 user subject 補抓 scaffolds + scaffold_node_links。

    根因：fork_platform_subject() 在 PR #37 前只複製 resources + nodes，
    沒帶 resource_scaffolds → 用戶看不到任何學習鷹架。

    修法：
    1. 從 source_platform_subject_id 找平台原始 subject
    2. 對應 platform_resource_id → user_resource_id 映射（透過 fork 時建的 GCS path 或 owner+name）
    3. 從平台 scaffolds 複製過來，新 ID + 重指 user_resource_id
    4. 建立 scaffold_node_links（embedding 對應 user nodes）

    僅 SUPER_ADMIN 可呼叫；冪等（重複呼叫只新增缺的 scaffolds）。
    """
    import uuid as _uuid
    from sqlalchemy import text
    from app.models.user import User, UserRole
    from app.models.subject import Subject
    from app.models.resource import Resource
    from app.models.resource_scaffold import ResourceScaffold

    try:
        user_uuid = _uuid.UUID(user_id)
        sid = _uuid.UUID(subject_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})
    user = db.query(User).filter_by(id=user_uuid).first()
    if not user or user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})

    user_subj = db.query(Subject).filter_by(id=sid).first()
    if not user_subj:
        raise HTTPException(status_code=404, detail={"message": "subject 不存在"})
    if not user_subj.source_platform_subject_id:
        return {"ok": False, "reason": "非 fork 來源科目（無 source_platform_subject_id）"}

    plat_sid = user_subj.source_platform_subject_id

    # 對應 user resources × platform resources（用 name 比對 — fork 時 name 不變）
    user_resources = db.query(Resource).filter(Resource.subject_id == sid).all()
    plat_resources = db.query(Resource).filter(Resource.subject_id == plat_sid).all()

    name_to_user_rid = {r.name: r.id for r in user_resources}
    plat_to_user_rid: dict[_uuid.UUID, _uuid.UUID] = {}
    for pr in plat_resources:
        if pr.name in name_to_user_rid:
            plat_to_user_rid[pr.id] = name_to_user_rid[pr.name]

    if not plat_to_user_rid:
        return {"ok": False, "reason": "資源 name 對應失敗，無法 repair"}

    scaffold_id_map: dict[_uuid.UUID, _uuid.UUID] = {}
    scaffolds_created = 0
    for plat_rid, user_rid in plat_to_user_rid.items():
        # 該 user resource 已有的 scaffolds（避免重複）
        existing = db.execute(text(
            "SELECT chapter_heading, type, content FROM resource_scaffolds WHERE resource_id = :rid"
        ), {"rid": str(user_rid)}).fetchall()
        existing_keys = {(r[0], r[1], r[2][:50] if r[2] else "") for r in existing}

        plat_scaffolds = db.query(ResourceScaffold).filter(
            ResourceScaffold.resource_id == plat_rid
        ).all()
        for ps in plat_scaffolds:
            key = (ps.chapter_heading, ps.type, ps.content[:50] if ps.content else "")
            if key in existing_keys:
                continue
            new_sid = _uuid.uuid4()
            scaffold_id_map[ps.id] = new_sid
            db.add(ResourceScaffold(
                id=new_sid,
                resource_id=user_rid,
                tenant_id=ps.tenant_id,
                chapter_heading=ps.chapter_heading,
                type=ps.type,
                content=ps.content,
                page_start=ps.page_start,
                page_end=ps.page_end,
                reference_answer=ps.reference_answer,
                retrieval_prompt=ps.retrieval_prompt,
                template_code=ps.template_code,
                embedding=ps.embedding,
            ))
            scaffolds_created += 1

    db.commit()

    # 觸發 relink 用 _link_scaffolds_to_nodes（如果 user nodes 有 embedding）
    relinked = 0
    if scaffolds_created > 0:
        from app.services.unified_knowledge_extraction_service import (
            UnifiedKnowledgeExtractionService
        )
        try:
            svc = UnifiedKnowledgeExtractionService(db)
            svc._embed_nodes_for_subject(sid)
            db.commit()
            relinked = svc._relink_subject_scaffolds(sid)
            db.commit()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("[repair-fork] relink failed")
            db.rollback()

    return {
        "ok": True,
        "subject_id": subject_id,
        "source_platform_id": str(plat_sid),
        "scaffolds_created": scaffolds_created,
        "relinked": relinked,
    }


# ── Deploy 健康檢查 — 主動驗 schema 狀態（不需 auth，CI 可呼） ──────────────

@router.get("/health/db-schema", include_in_schema=False)
def health_db_schema():
    """Schema 健康檢查 — Deploy 後 CI / smoke 主動驗。

    回傳：
    - alembic_version：當前 migration 版本
    - missing_tables / missing_columns：應有但 DB 沒有的（若有，表示 migration 未跑完）
    - status：healthy / degraded / unknown

    無 auth — 為了讓 CI / Cloud Run 健康檢查能呼叫。
    不暴露敏感資訊（schema 名稱本身為公開）。
    """
    from sqlalchemy import text
    from app.core.deps import get_db

    # 期待存在的關鍵 schema 元素（每加新 migration 應更新此清單）
    EXPECTED_TABLES = [
        "users", "subjects", "resources", "knowledge_nodes",
        "resource_scaffolds", "scaffold_node_links",
        "node_mastery", "node_mastery_orphans",
        "user_email_preferences", "email_send_log",
        "ai_model_routings",
    ]
    EXPECTED_COLUMNS = {
        # (table, column) — Sprint 7+ 新增的關鍵欄位
        ("resource_scaffolds", "embedding"): "Sprint 7 T54",
        ("knowledge_nodes", "embedding"): "Sprint 10 T80",
    }

    db_gen = get_db()
    db = next(db_gen)
    try:
        # 1. alembic version
        try:
            ver = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        except Exception:
            ver = None

        # 2. tables
        existing_tables = {
            r[0] for r in db.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )).fetchall()
        }
        missing_tables = [t for t in EXPECTED_TABLES if t not in existing_tables]

        # 3. critical columns
        missing_columns = []
        for (table, col), src in EXPECTED_COLUMNS.items():
            if table not in existing_tables:
                continue  # 表本身缺，已歸類在 missing_tables
            exists = db.execute(text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c"
            ), {"t": table, "c": col}).first()
            if not exists:
                missing_columns.append({"table": table, "column": col, "source": src})

        if missing_tables or missing_columns:
            status = "degraded"
        elif ver:
            status = "healthy"
        else:
            status = "unknown"

        return {
            "status": status,
            "alembic_version": ver,
            "missing_tables": missing_tables,
            "missing_columns": missing_columns,
            "table_count": len(existing_tables),
        }
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

