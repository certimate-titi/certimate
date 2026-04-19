"""GeminiCacheService — Tier 1-C Gemini Context Caching wrapper.

Two layers:
1. Explicit caching: when a system prompt is stable and ≥ minimum tokens,
   create a Gemini cached-content resource and reuse it by name.
2. Implicit caching: for shorter prompts Gemini 2.5 Flash auto-detects
   repeated prefixes; we only track `cached_content_token_count` in usage
   metadata to measure savings.

Design goals:
- Opt-in per caller (not a global intercept)
- Graceful fallback if cache create/use fails
- In-memory TTL mapping (prompt_hash → cache_name) valid 1 hour
- Env-var kill switch `GEMINI_EXPLICIT_CACHE_ENABLED=false` for rollback
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Explicit cache minimums published by Google (tokens).
# We refuse to create a cache if estimated tokens are below this.
_MIN_CACHE_TOKENS = {
    "gemini-2.5-flash": 4096,
    "gemini-2.5-pro": 32768,
    "gemini-2.0-flash": 4096,
}
_DEFAULT_MIN_CACHE_TOKENS = 4096


@dataclass
class _CacheEntry:
    name: str          # e.g. "cachedContents/abc123"
    created_at: float  # monotonic seconds
    ttl_seconds: int


class GeminiCacheService:
    """Thread-safe in-memory registry mapping prompt hashes → Gemini cache resources."""

    _instance: "GeminiCacheService | None" = None
    _lock = threading.RLock()

    def __new__(cls) -> "GeminiCacheService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._entries = {}  # type: ignore[attr-defined]
                    cls._instance._stats = {     # type: ignore[attr-defined]
                        "hits": 0,
                        "misses": 0,
                        "creates": 0,
                        "failures": 0,
                        "cached_tokens_seen": 0,
                    }
        return cls._instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_enabled(self) -> bool:
        return os.environ.get("GEMINI_EXPLICIT_CACHE_ENABLED", "true").lower() == "true"

    def get_or_create_cache(
        self,
        *,
        model: str,
        system_prompt: str,
        display_name: str,
        ttl_seconds: int = 3600,
    ) -> str | None:
        """Return a cache resource name for reuse, or None if caching not applicable.

        Strategy:
        1. Check TTL cache → return existing name if fresh
        2. Quick token estimate → skip if below minimum
        3. Try create cache via google-genai SDK
        4. On success, register in TTL cache
        5. On failure, return None (caller should proceed without cache)
        """
        if not self.is_enabled():
            return None

        cache_key = self._hash_prompt(model, system_prompt)

        # Layer 1: TTL-cache hit
        with self._lock:
            entry: _CacheEntry | None = self._entries.get(cache_key)  # type: ignore[attr-defined]
            if entry and (time.monotonic() - entry.created_at) < entry.ttl_seconds:
                self._stats["hits"] += 1  # type: ignore[attr-defined]
                return entry.name
            if entry:
                # Expired — drop it and fall through to re-create
                self._entries.pop(cache_key, None)  # type: ignore[attr-defined]

        # Layer 2: minimum-size gate
        est_tokens = max(len(system_prompt) // 4, 1)
        min_tokens = _MIN_CACHE_TOKENS.get(model, _DEFAULT_MIN_CACHE_TOKENS)
        if est_tokens < min_tokens:
            with self._lock:
                self._stats["misses"] += 1  # type: ignore[attr-defined]
            return None

        # Layer 3: create via SDK
        try:
            name = self._create_cache_via_sdk(
                model=model,
                system_prompt=system_prompt,
                display_name=display_name,
                ttl_seconds=ttl_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini cache create failed: %s", exc)
            with self._lock:
                self._stats["failures"] += 1  # type: ignore[attr-defined]
            return None

        with self._lock:
            self._entries[cache_key] = _CacheEntry(  # type: ignore[attr-defined]
                name=name,
                created_at=time.monotonic(),
                ttl_seconds=ttl_seconds,
            )
            self._stats["creates"] += 1  # type: ignore[attr-defined]
        logger.info("Gemini cache created: %s (display=%s)", name, display_name)
        return name

    def record_cached_tokens_seen(self, cached_tokens: int) -> None:
        """Called by LLMService after each generate_content to track implicit cache savings."""
        if cached_tokens <= 0:
            return
        with self._lock:
            self._stats["cached_tokens_seen"] += cached_tokens  # type: ignore[attr-defined]

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            total_lookups = self._stats["hits"] + self._stats["misses"]  # type: ignore[attr-defined]
            hit_rate = (
                self._stats["hits"] / total_lookups if total_lookups > 0 else 0.0  # type: ignore[attr-defined]
            )
            return {
                **dict(self._stats),  # type: ignore[arg-type]
                "active_entries": len(self._entries),  # type: ignore[attr-defined]
                "hit_rate": round(hit_rate, 3),
            }

    def invalidate_all(self) -> int:
        """Delete all entries from the in-memory mapping (does NOT delete on Google side)."""
        with self._lock:
            count = len(self._entries)  # type: ignore[attr-defined]
            self._entries.clear()  # type: ignore[attr-defined]
            return count

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _hash_prompt(self, model: str, content: str) -> str:
        h = hashlib.sha256()
        h.update(model.encode())
        h.update(b"|")
        h.update(content.encode())
        return h.hexdigest()[:32]

    def _create_cache_via_sdk(
        self,
        *,
        model: str,
        system_prompt: str,
        display_name: str,
        ttl_seconds: int,
    ) -> str:
        from google import genai
        from google.genai import types as genai_types

        settings = get_settings()
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        cached = client.caches.create(
            model=model,
            config=genai_types.CreateCachedContentConfig(
                display_name=display_name,
                system_instruction=system_prompt,
                ttl=f"{ttl_seconds}s",
            ),
        )
        return cached.name
