"""依賴注入模組 - E2E Testing.

Phase 2 更新：
- 新增 get_tenant_id() — 從 JWT payload 提取 tenant_id
- 新增 get_current_user_with_tenant() — 同時回傳 user_id + tenant_id
- 新增 set_rls_tenant() — 設定 PostgreSQL RLS 的 app.current_tenant_id
"""

from typing import Generator, NamedTuple
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.config import get_settings

# 預設 B2C 租戶 UUID（與 migration 038 一致）
PUBLIC_B2C_TENANT_ID = "00000000-0000-0000-0000-000000b2cb2c"

# 全域變數，由 environment.py 或應用程式啟動時設定
_SessionLocal = None

# HTTP Bearer Token scheme（auto_error=False 以自訂錯誤訊息）
security = HTTPBearer(auto_error=False)


class UserContext(NamedTuple):
    """用戶上下文，包含 user_id 與 tenant_id。"""
    user_id: str
    tenant_id: str


def set_session_factory(session_factory):
    """設定 Session Factory（由測試環境或應用程式初始化時呼叫）。"""
    global _SessionLocal
    _SessionLocal = session_factory


def get_db() -> Generator[Session, None, None]:
    """取得資料庫 Session。"""
    if _SessionLocal is None:
        raise RuntimeError(
            "Database session factory not initialized. "
            "Call set_session_factory() first."
        )

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _decode_jwt_payload(credentials: HTTPAuthorizationCredentials | None) -> dict:
    """內部輔助函式：解析 JWT 並回傳 payload。"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未認證，請先登入"
        )

    settings = get_settings()
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已過期"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的 Token"
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """從 JWT Token 中提取當前用戶 ID。"""
    payload = _decode_jwt_payload(credentials)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證憑證"
        )
    return user_id_str


def get_tenant_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """從 JWT Token 中提取 tenant_id。

    JWT payload 預期包含：
      {
        "sub": "<user_uuid>",
        "tenant_id": "<tenant_uuid>",   # Phase 2 新增
        "role": "student|teacher|admin",
        ...
      }
    若 Token 中不含 tenant_id，預設回傳 public_b2c 租戶 ID。
    """
    payload = _decode_jwt_payload(credentials)
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        # 向後相容：舊 Token 無 tenant_id → 歸屬預設 B2C 租戶
        return PUBLIC_B2C_TENANT_ID
    return str(tenant_id)


def get_current_user_with_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserContext:
    """同時提取 user_id 與 tenant_id，供需要租戶隔離的端點使用。

    使用範例：
        @router.post("/resources")
        async def create_resource(
            ctx: UserContext = Depends(get_current_user_with_tenant),
            db: Session = Depends(get_db),
        ):
            # 設定 RLS context
            set_rls_tenant(db, ctx.tenant_id)
            ...
    """
    payload = _decode_jwt_payload(credentials)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證憑證"
        )

    tenant_id = payload.get("tenant_id", PUBLIC_B2C_TENANT_ID)
    return UserContext(user_id=str(user_id), tenant_id=str(tenant_id))


def set_rls_tenant(db: Session, tenant_id: str) -> None:
    """在當前 DB Session 中設定 RLS 租戶 ID。

    搭配 migration 038 建立的 RLS policy：
      SET LOCAL app.current_tenant_id = '<uuid>'

    應在每個需要 RLS 的請求開始時呼叫。
    """
    # SET LOCAL 只在當前 transaction 有效，不會跨請求洩漏
    db.execute(
        __import__("sqlalchemy").text(
            "SET LOCAL app.current_tenant_id = :tid"
        ),
        {"tid": str(tenant_id)}
    )


def get_db_with_tenant(
    tenant_id: str = Depends(get_tenant_id),
) -> Generator[Session, None, None]:
    """取得已設定 RLS tenant context 的 DB Session。

    組合依賴注入：自動在 Session 開始時設定 app.current_tenant_id。
    供高安全性端點使用（如向量搜尋、成績存取）。
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database session factory not initialized. "
            "Call set_session_factory() first."
        )

    db = _SessionLocal()
    try:
        set_rls_tenant(db, tenant_id)
        yield db
    finally:
        db.close()
