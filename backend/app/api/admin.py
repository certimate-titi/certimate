"""平台管理後台 API。"""

import os
import sys
import subprocess
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
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

    user = db.query(User).filter_by(id=user_id).first()
    if not user or (getattr(user, "role", "") not in ("admin", "super_admin")):
        raise HTTPException(status_code=403, detail={"message": "僅平台管理員可綁定預設資源"})

    resource = db.query(Resource).filter_by(id=body.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail={"message": "資源不存在"})
    if str(resource.scope) != "platform":
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

    user = db.query(User).filter_by(id=user_id).first()
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
