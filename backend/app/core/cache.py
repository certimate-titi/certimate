"""輕量 KV 快取 — Redis 優先，記憶體 Fallback.

設計：
- 僅支援 JSON 序列化的資料
- 以 key prefix + TTL 做失效
- Redis 不可用時透明降級為 process-local dict（TTL 仍有效）

使用：
    from app.core.cache import cache
    data = cache.get(f"subject:{{sid}}:nodes")
    if data is None:
        data = compute()
        cache.set(f"subject:{{sid}}:nodes", data, ttl=60)
"""

from __future__ import annotations

import json
import logging
import os
import time
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() in ("true", "1", "yes")


class _MemoryCache:
    def __init__(self) -> None:
        self._lock = Lock()
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at, raw = entry
            if time.monotonic() > expires_at:
                self._store.pop(key, None)
                return None
            return json.loads(raw)

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + ttl, json.dumps(value, default=str))

    def delete_prefix(self, prefix: str) -> int:
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                self._store.pop(k, None)
            return len(keys)


class _RedisCache:
    def __init__(self, url: str) -> None:
        import redis  # lazy import
        self._r = redis.Redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=0.5)
        self._r.ping()

    def get(self, key: str) -> Any | None:
        raw = self._r.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._r.setex(key, ttl, json.dumps(value, default=str))

    def delete_prefix(self, prefix: str) -> int:
        count = 0
        for k in self._r.scan_iter(match=f"{prefix}*", count=200):
            self._r.delete(k)
            count += 1
        return count


class Cache:
    """Facade — 優先 Redis，失敗自動 fallback memory。"""

    def __init__(self) -> None:
        self._memory = _MemoryCache()
        self._redis: _RedisCache | None = None
        if _CACHE_ENABLED:
            try:
                self._redis = _RedisCache(_REDIS_URL)
                logger.info("Cache: Redis 已連線 (%s)", _REDIS_URL)
            except Exception as e:
                logger.warning("Cache: Redis 不可用，降級至記憶體 (%s)", e)

    def _backend(self):
        return self._redis or self._memory

    def get(self, key: str) -> Any | None:
        try:
            return self._backend().get(key)
        except Exception as e:
            logger.warning("Cache.get 失敗 key=%s err=%s", key, e)
            return self._memory.get(key)

    def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            self._backend().set(key, value, ttl)
        except Exception as e:
            logger.warning("Cache.set 失敗 key=%s err=%s", key, e)
            self._memory.set(key, value, ttl)

    def delete_prefix(self, prefix: str) -> int:
        try:
            return self._backend().delete_prefix(prefix)
        except Exception as e:
            logger.warning("Cache.delete_prefix 失敗 prefix=%s err=%s", prefix, e)
            return self._memory.delete_prefix(prefix)


cache = Cache()
