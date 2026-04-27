"""語意快取服務 — Semantic Cache（Redis + 記憶體 Fallback）.

架構說明：
- 快取鍵值：`semantic:{tenant_id}:{semantic_hash}`
- semantic_hash = SHA-256(normalized_prompt) — 精確匹配
- 語意相似匹配：透過向量餘弦相似度（需 embedding 支援），閾值可設定
- 儲存格式：JSON 序列化的 LLM 回應 + metadata
- TTL：預設 24 小時（可依 tenant 等級調整）

使用情境（OKR O3 KR1：LLM API 成本 ≤ 15% 營收）：
- AI 出題（相同 prompt → 相同考題）
- AI 知識心智圖生成（同一文件段落不重複呼叫）
- AI 教練回應（常見問題快取）

環境變數：
    REDIS_URL              Redis 連線字串（預設 redis://localhost:6379/0）
    SEMANTIC_CACHE_TTL     快取 TTL 秒數（預設 86400 = 24h）
    SEMANTIC_CACHE_ENABLED 是否啟用（預設 "true"）
    SEMANTIC_SIMILARITY_THRESHOLD  向量相似度閾值（預設 0.95）

使用方式：
    from app.services.semantic_cache_service import SemanticCacheService

    cache = SemanticCacheService()

    # 精確匹配（同 prompt 字串）
    cached = await cache.get(tenant_id, prompt)
    if cached:
        return cached

    result = await llm_call(prompt)
    await cache.set(tenant_id, prompt, result)
    return result
"""

import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class SemanticCacheConfig:
    """語意快取配置。"""

    def __init__(self):
        """初始化實例。"""
        self.enabled: bool = os.environ.get(
            "SEMANTIC_CACHE_ENABLED", "true"
        ).lower() in ("true", "1", "yes")
        self.redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.ttl: int = int(os.environ.get("SEMANTIC_CACHE_TTL", "86400"))  # 24h
        self.similarity_threshold: float = float(
            os.environ.get("SEMANTIC_SIMILARITY_THRESHOLD", "0.95")
        )


_config = SemanticCacheConfig()


# ── 記憶體快取（Redis 不可用時的 Fallback）──────────────────────────────────

class _InMemoryCache:
    """TTL-aware 記憶體快取（執行緒安全）。"""

    def __init__(self):
        """初始化實例。"""
        import threading
        self._lock = threading.Lock()
        # {key: (value, expire_at)}
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = 300.0  # 每 5 分鐘清理過期項目

    def _maybe_cleanup(self):
        """ maybe cleanup。"""
        now = time.monotonic()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        now_ts = time.time()
        expired = [k for k, (_, exp) in self._store.items() if exp < now_ts]
        for k in expired:
            del self._store[k]
        self._last_cleanup = now

    def get(self, key: str) -> Optional[Any]:
        """取得。"""
        with self._lock:
            self._maybe_cleanup()
            item = self._store.get(key)
            if item is None:
                return None
            value, expire_at = item
            if time.time() > expire_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """set。"""
        with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        """刪除。"""
        with self._lock:
            self._store.pop(key, None)

    def size(self) -> int:
        """size。"""
        with self._lock:
            self._maybe_cleanup()
            return len(self._store)


_memory_cache = _InMemoryCache()


# ── Redis 快取後端 ────────────────────────────────────────────────────────

class _RedisCache:
    """Redis 快取後端。"""

    def __init__(self, redis_url: str):
        """初始化實例。"""
        self._url = redis_url
        self._client = None
        self._available = False
        self._connect()

    def _connect(self):
        """ connect。"""
        try:
            import redis as redis_lib
            self._client = redis_lib.from_url(
                self._url,
                socket_connect_timeout=1,
                socket_timeout=0.5,
                decode_responses=True,
            )
            self._client.ping()
            self._available = True
            logger.info(f"✅ Semantic Cache Redis 連線成功：{self._url}")
        except ImportError:
            logger.warning("redis 套件未安裝，語意快取降級至記憶體模式")
        except Exception as e:
            logger.warning(f"Semantic Cache Redis 連線失敗（降級至記憶體）：{e}")

    def get(self, key: str) -> Optional[str]:
        """取得。"""
        if not self._available:
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET 失敗：{e}")
            self._available = False
            return None

    def set(self, key: str, value: str, ttl: int) -> None:
        """set。"""
        if not self._available:
            return
        try:
            self._client.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Redis SET 失敗：{e}")
            self._available = False

    def delete(self, key: str) -> None:
        """刪除。"""
        if not self._available:
            return
        try:
            self._client.delete(key)
        except Exception:
            pass

    def scan_prefix(self, prefix: str) -> list:
        """掃描符合前綴的所有 key（用於租戶快取清除）。"""
        if not self._available:
            return []
        try:
            keys = []
            cursor = 0
            while True:
                cursor, batch = self._client.scan(cursor, match=f"{prefix}*", count=100)
                keys.extend(batch)
                if cursor == 0:
                    break
            return keys
        except Exception as e:
            logger.warning(f"Redis SCAN 失敗：{e}")
            return []


# ── 全域後端實例 ────────────────────────────────────────────────────────────

_redis_cache: Optional[_RedisCache] = None
import threading as _threading
_redis_init_lock = _threading.Lock()


def _get_redis() -> Optional[_RedisCache]:
    """取得 redis。"""
    global _redis_cache
    if _redis_cache is None:
        with _redis_init_lock:
            if _redis_cache is None:
                _redis_cache = _RedisCache(_config.redis_url)
    return _redis_cache


# ── 雜湊工具 ────────────────────────────────────────────────────────────────

def _semantic_hash(prompt: str) -> str:
    """計算 prompt 的語意 hash（SHA-256）。

    正規化處理：
    - 小寫、去除多餘空白，確保 "Help me" 與 "help me" 命中同一快取。
    """
    normalized = " ".join(prompt.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def _make_key(tenant_id: str, prompt_hash: str) -> str:
    """建立 key。"""
    return f"semantic:{tenant_id}:{prompt_hash}"


# ── SemanticCacheService ─────────────────────────────────────────────────────

class SemanticCacheService:
    """語意快取服務 — LLM 回應快取，降低重複生成成本.

    支援精確匹配（SHA-256 hash）。
    未來可擴展為向量相似度匹配（需整合 embedding_service.py）。
    """

    def __init__(self, ttl: Optional[int] = None):
        """初始化實例。"""
        self._ttl = ttl or _config.ttl

    async def get(
        self,
        tenant_id: str,
        prompt: str,
        *,
        context: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """查詢快取。

        Args:
            tenant_id: 租戶 ID（快取隔離）
            prompt: LLM prompt 文字
            context: 額外上下文（如 subject_id、document_id），加入 hash 計算

        Returns:
            快取的 LLM 回應 dict，或 None（快取未命中）
        """
        if not _config.enabled:
            return None

        full_prompt = f"{prompt}|{context}" if context else prompt
        key = _make_key(tenant_id, _semantic_hash(full_prompt))

        # 先查 Redis
        redis = _get_redis()
        cached_str: Optional[str] = None

        if redis and redis._available:
            cached_str = redis.get(key)
        else:
            # Fallback 至記憶體
            cached_val = _memory_cache.get(key)
            if cached_val is not None:
                logger.debug(f"Semantic cache HIT (memory): {key[:40]}...")
                return cached_val

        if cached_str:
            try:
                result = json.loads(cached_str)
                logger.debug(f"Semantic cache HIT (redis): {key[:40]}...")
                return result
            except json.JSONDecodeError:
                logger.warning(f"快取值 JSON 解析失敗，刪除損壞快取：{key}")
                redis.delete(key)

        return None

    async def set(
        self,
        tenant_id: str,
        prompt: str,
        response: Dict[str, Any],
        *,
        context: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """寫入快取。

        Args:
            tenant_id: 租戶 ID
            prompt: LLM prompt 文字
            response: LLM 回應 dict（必須可 JSON 序列化）
            context: 額外上下文
            ttl: 覆蓋預設 TTL（秒）
        """
        if not _config.enabled:
            return

        full_prompt = f"{prompt}|{context}" if context else prompt
        key = _make_key(tenant_id, _semantic_hash(full_prompt))
        effective_ttl = ttl or self._ttl

        # 加入快取 metadata
        cache_entry = {
            **response,
            "__cached_at": time.time(),
            "__cache_ttl": effective_ttl,
        }

        redis = _get_redis()
        if redis and redis._available:
            try:
                redis.set(key, json.dumps(cache_entry, ensure_ascii=False), effective_ttl)
                logger.debug(f"Semantic cache SET (redis): {key[:40]}...")
                return
            except Exception as e:
                logger.warning(f"Redis cache SET 失敗（降級至記憶體）：{e}")

        # Fallback 至記憶體
        _memory_cache.set(key, cache_entry, effective_ttl)
        logger.debug(f"Semantic cache SET (memory): {key[:40]}...")

    async def invalidate(self, tenant_id: str, prompt: str, *, context: Optional[str] = None) -> None:
        """主動清除特定快取項目。"""
        full_prompt = f"{prompt}|{context}" if context else prompt
        key = _make_key(tenant_id, _semantic_hash(full_prompt))

        redis = _get_redis()
        if redis:
            redis.delete(key)
        _memory_cache.delete(key)

    async def invalidate_tenant(self, tenant_id: str) -> int:
        """清除指定租戶的所有快取（租戶退場或大規模更新時使用）。

        Returns:
            清除的快取項目數量
        """
        prefix = f"semantic:{tenant_id}:"
        count = 0

        redis = _get_redis()
        if redis and redis._available:
            keys = redis.scan_prefix(prefix)
            for key in keys:
                redis.delete(key)
                count += len(keys)

        # 記憶體快取暫不支援前綴刪除（數量通常少，影響小）
        logger.info(f"租戶 {tenant_id} 語意快取清除完成：{count} 條")
        return count

    def stats(self) -> Dict[str, Any]:
        """回傳快取統計資訊（監控用）。"""
        redis = _get_redis()
        return {
            "enabled": _config.enabled,
            "redis_available": bool(redis and redis._available),
            "memory_cache_size": _memory_cache.size(),
            "ttl_seconds": self._ttl,
            "similarity_threshold": _config.similarity_threshold,
        }


# ── 全域單例 ──────────────────────────────────────────────────────────────

_semantic_cache_instance: Optional[SemanticCacheService] = None


def get_semantic_cache() -> SemanticCacheService:
    """取得語意快取服務單例（FastAPI Depends 用）。"""
    global _semantic_cache_instance
    if _semantic_cache_instance is None:
        _semantic_cache_instance = SemanticCacheService()
    return _semantic_cache_instance
