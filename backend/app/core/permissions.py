"""Permission dependencies for role-based access control.

Feature 33 — 成本監控中心
提供 require_super_admin() FastAPI dependency，用於限制僅 Super Admin 可存取的 API。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.deps import _decode_jwt_payload, get_db, security
from app.models.user import User, UserRole


def require_super_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: 僅允許 super_admin 角色存取。

    檢查順序：
    1. 解析 JWT → 取得 user_id
    2. 從 DB 查詢 User.role（JWT claim 不可信，以 DB 為真實來源）
    3. 若 role != SUPER_ADMIN → 403 FORBIDDEN_SUPER_ADMIN_ONLY

    使用範例：
        @router.get("/admin/cost/summary")
        def get_cost_summary(
            super_admin: User = Depends(require_super_admin),
        ):
            ...

    Raises:
        HTTPException 401: JWT 無效
        HTTPException 403: 角色非 super_admin
    """
    payload = _decode_jwt_payload(credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "無效的認證憑證", "code": "INVALID_CREDENTIALS"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "使用者不存在", "code": "USER_NOT_FOUND"},
        )

    if user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "此操作僅限 Super Admin",
                "code": "FORBIDDEN_SUPER_ADMIN_ONLY",
            },
        )

    return user


def require_admin_or_super_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: 允許 admin 或 super_admin 角色存取。

    用於既有 admin router 的向後相容場景。成本監控不使用此 dependency。
    """
    payload = _decode_jwt_payload(credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "無效的認證憑證", "code": "INVALID_CREDENTIALS"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "此操作僅限管理員", "code": "FORBIDDEN_ADMIN_ONLY"},
        )

    return user


# ---------------------------------------------------------------------------
# Feature 33 — admin_audit_log action 常數
# ---------------------------------------------------------------------------

class AuditAction:
    """Centralized audit action constants for Feature 33 cost monitor.

    所有 Super Admin 對成本監控的操作都應使用此常數寫入 admin_audit_logs，
    避免字串拼寫錯誤導致稽核查詢漏失。
    """

    # 讀取操作
    COST_MONITOR_VIEWED = "COST_MONITOR_VIEWED"

    # 預算修改
    BUDGET_UPDATED = "BUDGET_UPDATED"
    BUDGET_GLOBAL_SCALED = "BUDGET_GLOBAL_SCALED"
    BUDGET_GLOBAL_SET = "BUDGET_GLOBAL_SET"

    # 狀態操作
    BUDGET_OVERRIDE = "BUDGET_OVERRIDE"
    BUDGET_RECOVERY_TRIGGERED = "BUDGET_RECOVERY_TRIGGERED"

    # 硬刪除（P0 — 不可逆操作）
    SUBJECT_HARD_DELETED = "SUBJECT_HARD_DELETED"
    RESOURCE_HARD_DELETED = "RESOURCE_HARD_DELETED"


# ---------------------------------------------------------------------------
# Feature 33 — Budget gate dependency
# ---------------------------------------------------------------------------


def require_ai_budget_available(db: Session = Depends(get_db)) -> None:
    """FastAPI dependency: 阻擋 AI 生成類 endpoint 當 AI scope 進入 degraded/disabled。

    根據哪個 scope 的狀態決定錯誤代碼：
    - 任一 scope disabled → 403 AI_BUDGET_EXHAUSTED
    - 任一 scope degraded → 403 AI_BUDGET_DEGRADED
    - 否則放行
    """
    from app.models.budget_config import BudgetConfig

    rows = (
        db.query(BudgetConfig)
        .filter(BudgetConfig.scope.in_(("AI_ANTHROPIC", "AI_GEMINI", "AI_VOYAGE")))
        .all()
    )
    has_disabled = any(r.current_state == "disabled" for r in rows)
    has_degraded = any(r.current_state == "degraded" for r in rows)

    if has_disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AI_BUDGET_EXHAUSTED",
                "message": "AI 月度預算已耗盡，請聯繫管理員",
            },
        )
    if has_degraded:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AI_BUDGET_DEGRADED",
                "message": "AI 預算已達降級門檻，新生成功能暫時停用",
            },
        )
