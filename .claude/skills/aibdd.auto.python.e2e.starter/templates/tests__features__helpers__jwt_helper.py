"""JWT Token 生成器 - 測試專用。"""

from datetime import datetime, timedelta
from typing import Optional

import jwt

from {{PY_APP_MODULE}}.core.config import get_settings


class JwtHelper:
    """JWT Token 生成器（測試專用）。

    用於在 E2E 測試中生成有效的 JWT Token，
    模擬已認證的用戶進行 API 請求。
    """

    def __init__(self, secret_key: Optional[str] = None):
        settings = get_settings()
        self.secret_key = secret_key or settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_hours = settings.JWT_EXPIRE_HOURS

    def generate_token(
        self,
        user_id,
        extra_claims: Optional[dict] = None,
        expire_hours: Optional[int] = None
    ) -> str:
        """生成 JWT Token。"""
        expire = datetime.utcnow() + timedelta(
            hours=expire_hours or self.expire_hours
        )

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        """解碼 JWT Token（用於測試驗證）。"""
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
