"""API Key 健康監控與管理 Service（Bug 8 — son731202 雲端 401 事件後新增）。

Spec 12c §「API Key 健康監控與管理」 — 提供 4 把 LLM key 的：
- ping 測試（1-token 最小 generate 請求）
- Secret Manager 寫入（雲端）/ .env 提示（本地）
- 失效時 email 通知 SUPER_ADMIN
- 狀態快取於記憶體（避免 N+1）

Providers: anthropic, gemini, voyage, openai
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

Provider = Literal["anthropic", "gemini", "voyage", "openai"]
PROVIDERS: tuple[Provider, ...] = ("anthropic", "gemini", "voyage", "openai")

# In-memory cache for last health check; keyed by provider
# 雲端多實例會各自獨立 — 之後可移到 Redis / DB
_health_cache: dict[Provider, dict] = {}


def _last_4(key: str | None) -> str:
    """取 key 後 4 碼（缺值回 '----'）。"""
    if not key or len(key) < 4:
        return "----"
    return key[-4:]


def _get_secret_manager_client():
    """雲端：取得 Secret Manager client（缺套件回 None，本地走 .env）。"""
    try:
        from google.cloud import secretmanager
        return secretmanager.SecretManagerServiceClient()
    except Exception as e:
        logger.info(f"Secret Manager unavailable (likely local dev): {e}")
        return None


class ApiKeyHealthService:
    """API Key 健康狀態 + 寫入服務。"""

    def __init__(self, db: Session):
        self.db = db
        self.email = EmailService()

    # ─── Status ──────────────────────────────────────────────────────────

    def get_all_statuses(self) -> dict:
        """回傳所有 provider 的健康狀態（含 last_4 / last_check_at）。"""
        from app.core.config import get_settings
        settings = get_settings()
        result = []
        for p in PROVIDERS:
            key = self._current_key(settings, p)
            cached = _health_cache.get(p, {})
            result.append({
                "provider": p,
                "last_4": _last_4(key),
                "configured": bool(key),
                "healthy": cached.get("healthy"),
                "last_check_at": cached.get("last_check_at"),
                "last_failure_reason": cached.get("last_failure_reason"),
            })
        return {"keys": result}

    def _current_key(self, settings, provider: Provider) -> str | None:
        """從 settings 讀目前 key。"""
        return {
            "anthropic": settings.ANTHROPIC_API_KEY,
            "gemini": settings.GEMINI_API_KEY,
            "voyage": settings.VOYAGE_API_KEY,
            "openai": settings.OPENAI_API_KEY,
        }.get(provider)

    # ─── Ping test ───────────────────────────────────────────────────────

    def test_key(self, provider: Provider, key_override: str | None = None) -> dict:
        """對 provider 發送 1-token 最小 generate 請求驗證 key 有效。

        Spec Q4: 測試 = 1-token ping，cost ~$0.000001。
        若 key_override 提供，測該 key 而非 settings 中的（用於儲存前驗證）。
        """
        from app.core.config import get_settings
        settings = get_settings()
        key = key_override or self._current_key(settings, provider)
        if not key:
            return self._update_cache(provider, healthy=False, reason="未設定 API key")

        try:
            if provider == "anthropic":
                self._ping_anthropic(key)
            elif provider == "gemini":
                self._ping_gemini(key)
            elif provider == "voyage":
                self._ping_voyage(key)
            elif provider == "openai":
                self._ping_openai(key)
            return self._update_cache(provider, healthy=True, reason=None)
        except Exception as e:
            reason = str(e)[:300]
            result = self._update_cache(provider, healthy=False, reason=reason)
            # Spec Q3: 每次失敗即通知 super-admin
            self._notify_failure(provider, reason)
            return result

    def _ping_anthropic(self, key: str):
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )

    def _ping_gemini(self, key: str):
        from google import genai
        client = genai.Client(api_key=key)
        client.models.generate_content(
            model="gemini-2.5-flash",
            contents="hi",
            config={"max_output_tokens": 1},
        )

    def _ping_voyage(self, key: str):
        import voyageai
        client = voyageai.Client(api_key=key)
        client.embed(["hi"], model="voyage-3", input_type="query")

    def _ping_openai(self, key: str):
        import openai
        client = openai.OpenAI(api_key=key)
        client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )

    # ─── Cache update + notify ───────────────────────────────────────────

    def _update_cache(self, provider: Provider, healthy: bool, reason: str | None) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        _health_cache[provider] = {
            "healthy": healthy,
            "last_check_at": now,
            "last_failure_reason": reason,
        }
        return {
            "provider": provider,
            "healthy": healthy,
            "last_check_at": now,
            "last_failure_reason": reason,
        }

    def _notify_failure(self, provider: Provider, reason: str) -> None:
        """寄信通知所有 SUPER_ADMIN。Spec Q3: 每次失敗即通知。"""
        try:
            super_admins = self.db.query(User).filter(
                User.role == UserRole.SUPER_ADMIN
            ).all()
            subject = f"[CertiMate] API Key 異常通知 — {provider}"
            body = (
                f"<p>偵測到 <b>{provider}</b> API Key 失效。</p>"
                f"<p>失敗原因：<code>{reason[:200]}</code></p>"
                f"<p>請至「平台管理 / 系統設定 / API Keys」重設此 key。</p>"
                f"<p>時間：{datetime.now(timezone.utc).isoformat()}</p>"
            )
            for admin in super_admins:
                if admin.email:
                    try:
                        self.email._send(admin.email, subject, body)
                    except Exception as e:
                        logger.warning(f"notify {admin.email} failed: {e}")
        except Exception as e:
            logger.exception(f"_notify_failure error: {e}")

    # ─── Update key (Secret Manager) ─────────────────────────────────────

    def update_key(self, actor_id: str, provider: Provider, new_key: str) -> dict:
        """寫入新 key。雲端走 Secret Manager；本地僅 log 提示（不動 .env）。

        Spec Q5: 僅 SUPER_ADMIN 可呼叫（router 層檢查），audit log 記 actor/timestamp/provider。
        Audit log 不記 key 內容，只記 last_4。
        """
        if not new_key or len(new_key) < 10:
            return {"error": True, "status_code": 400, "message": "API key 長度不足"}

        # 先 ping 測試新 key 是否有效（避免存壞 key）
        test_result = self.test_key(provider, key_override=new_key)
        if not test_result.get("healthy"):
            return {
                "error": True,
                "status_code": 400,
                "message": f"API key 測試失敗：{test_result.get('last_failure_reason')}",
            }

        # 雲端寫入 Secret Manager
        secret_id = {
            "anthropic": "anthropic-api-key",
            "gemini": "gemini-api-key",
            "voyage": "voyage-api-key",
            "openai": "openai-api-key",
        }[provider]

        sm_client = _get_secret_manager_client()
        backend = "secret-manager"
        if sm_client:
            project_id = os.environ.get("GCP_PROJECT_ID", "certimate-titi")
            parent = f"projects/{project_id}/secrets/{secret_id}"
            try:
                sm_client.add_secret_version(
                    request={"parent": parent, "payload": {"data": new_key.encode("utf-8")}}
                )
                logger.info(f"Secret Manager: added new version for {secret_id}")
            except Exception as e:
                return {"error": True, "status_code": 500, "message": f"Secret Manager 寫入失敗：{e}"}
        else:
            # 本地 dev：不寫 .env（避免 commit 風險），提示 admin 手動更新
            backend = "local-dev-instructed"
            logger.warning(
                f"[local] {provider} key 變更未持久化。"
                f"請手動更新 .env 並重啟 server（last_4={_last_4(new_key)}）"
            )

        # Audit log（不記 key 內容；target_id 用 NULL，provider 寫到 details）
        try:
            import uuid as _uuid
            self.db.add(AuditLog(
                admin_id=_uuid.UUID(actor_id),
                action="update_api_key",
                target_type="api_key",
                target_id=None,
                details={
                    "provider": provider,
                    "last_4": _last_4(new_key),
                    "backend": backend,
                },
            ))
            self.db.commit()
        except Exception as e:
            logger.warning(f"audit log write failed (non-fatal): {e}")

        return {
            "ok": True,
            "provider": provider,
            "last_4": _last_4(new_key),
            "backend": backend,
            "message": f"{provider} API key 已儲存（{backend}）；雲端需等待 Cloud Run 重啟才生效",
        }
