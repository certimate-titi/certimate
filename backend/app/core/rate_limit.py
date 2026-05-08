"""多租戶限流模組 — Redis Token Bucket + 記憶體 Fallback.

架構說明：
- Redis Token Bucket 算法：依租戶等級設定不同 QPS 限制
- 優雅降級：Redis 不可用時自動切換至記憶體實作（TTL dict）
- FastAPI Middleware：透明整合，無需修改各 route handler

租戶等級 QPS 限制（可透過環境變數覆蓋）：
    B2C_FREE_QPS       B2C 免費版：預設 10 req/s
    B2C_PRO_QPS        B2C PRO 版：預設 30 req/s
    B2C_ULTRA_QPS      B2C Ultra 版：預設 100 req/s
    B2B_QPS            B2B 機構版：預設 200 req/s
    DEFAULT_QPS        未認證 / 未知：預設 5 req/s

環境變數：
    RATE_LIMIT_ENABLED   是否啟用限流（預設 "true"）
    REDIS_URL            Redis 連線字串（預設 "redis://localhost:6379/0"）
    RATE_LIMIT_WINDOW    Token Bucket 時間窗口秒數（預設 "1"，即每秒重置）

使用方式（main.py）：
    from app.core.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

HTTP 回應：
    429 Too Many Requests + Retry-After header

OTel 整合：
    限流事件會記錄至 telemetry span（若 OTel 啟用）
"""

import os
import time
import asyncio
import logging
import threading
from collections import defaultdict
from typing import Optional, Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ── QPS 配置 ───────────────────────────────────────────────────────────────

class RateLimitConfig:
    """限流配置，從環境變數讀取。"""

    def __init__(self):
        self.enabled: bool = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
        self.redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.window_seconds: int = int(os.environ.get("RATE_LIMIT_WINDOW", "1"))

        # QPS 限制（請求 / 時間窗口）
        # 2026-05-08 smoke fix：reading 頁開啟瞬間並發 7+ 筆 interactions log
        # + chapter-practice，原 FREE=10 直接 429。提高基線並加 default=10 以
        # 兼容尚未含 plan claim 的 JWT。
        self.limits: Dict[str, int] = {
            "b2c_free":    int(os.environ.get("B2C_FREE_QPS", "30")),
            "b2c_pro":     int(os.environ.get("B2C_PRO_QPS", "60")),
            "b2c_ultra":   int(os.environ.get("B2C_ULTRA_QPS", "200")),
            "b2b":         int(os.environ.get("B2B_QPS", "400")),
            "default":     int(os.environ.get("DEFAULT_QPS", "10")),
        }


_config = RateLimitConfig()


# ── Backend：記憶體 Token Bucket（Redis 不可用時的 Fallback）───────────────

class _InMemoryTokenBucket:
    """執行緒安全的記憶體 Token Bucket。

    使用 (tenant_id, window_key) 作為 bucket 鍵值，每個時間窗口獨立計數。
    """

    def __init__(self):
        self._lock = threading.Lock()
        # {(tenant_id, window_key): count}
        self._buckets: Dict[Tuple[str, int], int] = defaultdict(int)
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = 60.0  # 每分鐘清理過期 bucket

    def _maybe_cleanup(self):
        """週期性清理過期 bucket（避免記憶體無限增長）。"""
        now = time.monotonic()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        current_window = int(time.time() / _config.window_seconds)
        stale_keys = [
            k for k in self._buckets
            if k[1] < current_window - 2  # 保留當前 + 前一個窗口
        ]
        for k in stale_keys:
            del self._buckets[k]
        self._last_cleanup = now

    def check_and_increment(self, tenant_key: str, limit: int) -> Tuple[bool, int]:
        """檢查並遞增計數器。

        Returns:
            (allowed, remaining_tokens)
        """
        window_key = int(time.time() / _config.window_seconds)
        bucket_key = (tenant_key, window_key)

        with self._lock:
            self._maybe_cleanup()
            current = self._buckets[bucket_key]
            if current >= limit:
                return False, 0
            self._buckets[bucket_key] += 1
            return True, max(0, limit - current - 1)


# ── Backend：Redis Token Bucket ────────────────────────────────────────────

class _RedisTokenBucket:
    """Redis 版 Token Bucket（Lua script 原子操作）。"""

    _LUA_SCRIPT = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])

    local current = redis.call('GET', key)
    if current == false then
        redis.call('SET', key, 1, 'EX', window)
        return {1, limit - 1}
    end

    current = tonumber(current)
    if current >= limit then
        return {0, 0}
    end

    redis.call('INCR', key)
    local ttl = redis.call('TTL', key)
    return {1, limit - current - 1}
    """

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._client = None
        self._script_sha = None
        self._available = False
        self._connect()

    def _connect(self):
        """嘗試連接 Redis。"""
        try:
            import redis as redis_lib
            self._client = redis_lib.from_url(
                self._redis_url,
                socket_connect_timeout=1,
                socket_timeout=0.5,
                decode_responses=False,
            )
            self._client.ping()
            self._script_sha = self._client.script_load(self._LUA_SCRIPT)
            self._available = True
            logger.info(f"✅ Rate Limit Redis 連線成功：{self._redis_url}")
        except ImportError:
            logger.warning("redis 套件未安裝，限流降級至記憶體模式")
        except Exception as e:
            logger.warning(f"Rate Limit Redis 連線失敗（降級至記憶體）：{e}")

    def check_and_increment(self, tenant_key: str, limit: int) -> Tuple[bool, int]:
        """執行 Redis Lua Script 原子計數。"""
        if not self._available or self._client is None:
            return None, None  # 表示 Redis 不可用，由 Fallback 處理

        window_key = int(time.time() / _config.window_seconds)
        key = f"ratelimit:{tenant_key}:{window_key}"

        try:
            result = self._client.evalsha(
                self._script_sha,
                1,  # numkeys
                key,
                str(limit),
                str(_config.window_seconds),
                str(int(time.time())),
            )
            allowed = int(result[0]) == 1
            remaining = int(result[1])
            return allowed, remaining
        except Exception as e:
            logger.warning(f"Redis 限流操作失敗（降級至記憶體）：{e}")
            self._available = False
            return None, None


# ── 全域後端實例 ────────────────────────────────────────────────────────────

_redis_backend: Optional[_RedisTokenBucket] = None
_memory_backend = _InMemoryTokenBucket()
_backend_lock = threading.Lock()


def _get_backends() -> Tuple[Optional[_RedisTokenBucket], _InMemoryTokenBucket]:
    global _redis_backend
    if _redis_backend is None:
        with _backend_lock:
            if _redis_backend is None:
                _redis_backend = _RedisTokenBucket(_config.redis_url)
    return _redis_backend, _memory_backend


# ── 訂閱方案 → 限流等級映射 ────────────────────────────────────────────────

_PLAN_TO_TIER = {
    # B2C
    "FREE":            "b2c_free",
    "PRO_199":         "b2c_pro",
    "PRO_PLUS_399":    "b2c_pro",
    "ULTRA_1599":      "b2c_ultra",
    # B2B
    "EDU":             "b2b",
    "INSTITUTION":     "b2b",
}


def _extract_tenant_info(request: Request) -> Tuple[str, int]:
    """從 Request 提取租戶限流 key 與對應 QPS 限制。

    優先順序：JWT payload > IP（未認證流量）
    """
    tenant_key = "anon"
    tier = "default"

    # 嘗試從 Authorization header 提取 tenant_id
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt
            from app.core.config import get_settings
            settings = get_settings()
            token = auth_header[7:]
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False},  # 限流不需要嚴格驗證 exp
            )
            tenant_id = payload.get("tenant_id") or payload.get("sub", "")
            plan = payload.get("plan", "FREE")
            if tenant_id:
                tenant_key = str(tenant_id)
                tier = _PLAN_TO_TIER.get(plan, "b2c_free")
        except Exception:
            pass  # JWT 解析失敗，降級為 IP 限流

    # 未認證流量 → 使用 IP 作為 key
    if tenant_key == "anon":
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (
            request.client.host if request.client else "unknown"
        )
        tenant_key = f"ip:{client_ip}"

    limit = _config.limits.get(tier, _config.limits["default"])
    return tenant_key, limit


# ── FastAPI Middleware ─────────────────────────────────────────────────────

# 豁免路徑（健康檢查、文件頁不計入限流）
_EXEMPT_PATHS = {
    "/health",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
}

# 豁免路徑前綴 — 分析型/UX 紀錄寫入不應佔用戶 QPS 配額
# （reading 頁載入會瞬間並發多筆 interactions log，會誤觸 free QPS 限制）
_EXEMPT_PREFIXES: Tuple[str, ...] = (
    "/api/v1/resource-scaffolds/",  # POST {id}/interactions：scaffold 互動 log
)


def _is_exempt(path: str) -> bool:
    if path in _EXEMPT_PATHS:
        return True
    return any(path.startswith(p) and path.endswith("/interactions") for p in _EXEMPT_PREFIXES)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """多租戶限流 Middleware — Token Bucket 算法。

    用法（main.py）：
        from app.core.rate_limit import RateLimitMiddleware
        app.add_middleware(RateLimitMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        # 未啟用或豁免路徑 → 直接通過
        if not _config.enabled or _is_exempt(request.url.path):
            return await call_next(request)
        # CORS preflight (OPTIONS) 不應計入限流 — 瀏覽器會為每個跨域請求自動發送
        if request.method == "OPTIONS":
            return await call_next(request)

        tenant_key, limit = _extract_tenant_info(request)
        redis_b, memory_b = _get_backends()

        # 先嘗試 Redis，失敗時 fallback 至記憶體
        allowed: Optional[bool] = None
        remaining: int = 0

        if redis_b is not None:
            allowed, remaining = redis_b.check_and_increment(tenant_key, limit)

        if allowed is None:  # Redis 不可用，使用記憶體
            allowed, remaining = memory_b.check_and_increment(tenant_key, limit)

        if not allowed:
            retry_after = _config.window_seconds
            logger.warning(
                f"Rate limit exceeded: tenant={tenant_key} path={request.url.path}"
            )
            # OTel 記錄
            try:
                from app.core.telemetry import get_tracer
                with get_tracer("rate_limit").start_as_current_span("rate_limit_exceeded") as span:
                    span.set_attribute("tenant_key", tenant_key)
                    span.set_attribute("http.path", request.url.path)
            except Exception:
                pass

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "請求過於頻繁，請稍後再試",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        response = await call_next(request)

        # 注入限流回應 headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() / _config.window_seconds + 1) * _config.window_seconds
        )
        return response
