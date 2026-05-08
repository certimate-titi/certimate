"""LLMService — Multi-provider LLM router.

Routes requests to Claude / OpenAI / Gemini based on:
1. ai_model_routings table (per plan + task_type)
2. Fallback to config defaults

Supports: text generation, PDF parsing, image OCR, JSON generation.
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_model_routing import AiModelRouting

logger = logging.getLogger(__name__)

# Provider detection by model name prefix
PROVIDER_MAP = {
    "claude": "anthropic",
    "gpt": "openai",
    "o1": "openai",
    "o3": "openai",
    "gemini": "google",
}


def _detect_provider(model_name: str) -> str:
    """Detect provider from model name."""
    lower = model_name.lower()
    for prefix, provider in PROVIDER_MAP.items():
        if lower.startswith(prefix):
            return provider
    return "anthropic"  # default


class LLMService:
    """Unified LLM interface that routes to the correct provider."""

    def __init__(self, db: Session | None = None):
        """初始化實例。"""
        self.db = db
        self.settings = get_settings()
        self._clients: dict = {}

    # ----------------------------------------------------------
    # Client lazy initialization
    # ----------------------------------------------------------

    def _get_anthropic(self):
        """取得 anthropic。"""
        if "anthropic" not in self._clients:
            import anthropic
            self._clients["anthropic"] = anthropic.Anthropic(
                api_key=self.settings.ANTHROPIC_API_KEY
            )
        return self._clients["anthropic"]

    @staticmethod
    def _use_claude_cli() -> bool:
        """本地開發環境是否走 Claude Code CLI subprocess（避免使用 API key）。

        env LLM_LOCAL_BACKEND=claude-code 時啟用；雲端部署不設此 env 即走 API。
        """
        import os
        return os.environ.get("LLM_LOCAL_BACKEND", "").lower() == "claude-code"

    def _generate_claude_cli(
        self, model: str, system_prompt: str, user_prompt: str, max_tokens: int
    ) -> str:
        """本地：透過 Claude Code CLI subprocess 跑 LLM（無 API 費用）。

        參考 exam-bank/parsers/claude_cli_converter.py 的 pattern。
        模型名稱透過 alias 對應（sonnet/opus/haiku）；不傳 --model 走 CLI 預設。
        """
        import os
        import subprocess

        cli_path = os.environ.get("CLAUDE_CLI_PATH", "claude")
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        try:
            proc = subprocess.run(
                [cli_path, "-p", full_prompt],
                capture_output=True,
                text=True,
                timeout=180,
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                f"Claude CLI not found at '{cli_path}'. Install Claude Code or set CLAUDE_CLI_PATH"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Claude CLI timeout (180s) for model={model}") from e
        if proc.returncode != 0:
            raise RuntimeError(
                f"Claude CLI failed (exit={proc.returncode}): {proc.stderr[:300]}"
            )
        return proc.stdout.strip()

    def _get_openai(self):
        """取得 openai。"""
        if "openai" not in self._clients:
            import openai
            self._clients["openai"] = openai.OpenAI(
                api_key=self.settings.OPENAI_API_KEY
            )
        return self._clients["openai"]

    def _get_google(self):
        """取得 google。"""
        if "google" not in self._clients:
            from google import genai
            self._clients["google"] = genai.Client(
                api_key=self.settings.GEMINI_API_KEY
            )
        return self._clients["google"]

    # ----------------------------------------------------------
    # Model resolution: DB routing → config fallback
    # ----------------------------------------------------------

    def resolve_model(
        self,
        plan: str = "FREE",
        task_type: str = "basic",
    ) -> tuple[str, str]:
        """Resolve which model to use for a given plan + task_type.

        Returns: (model_name, provider)

        Lookup order:
        1. ai_model_routings table (if db session available)
        2. Config defaults based on provider availability
        """
        # Try DB routing
        if self.db:
            routing = self.db.query(AiModelRouting).filter_by(
                plan=plan, task_type=task_type
            ).first()
            if routing:
                model = routing.primary_model
                provider = _detect_provider(model)
                # Verify the provider's API key is available
                if self._has_key(provider):
                    return model, provider
                # Try fallback model
                if routing.fallback_model:
                    fb_provider = _detect_provider(routing.fallback_model)
                    if self._has_key(fb_provider):
                        logger.info(
                            "Primary model %s unavailable (no %s key), using fallback %s",
                            model, provider, routing.fallback_model
                        )
                        return routing.fallback_model, fb_provider

        # Config defaults — pick first available provider
        if self.settings.ANTHROPIC_API_KEY:
            return self.settings.CLAUDE_MODEL, "anthropic"
        if self.settings.OPENAI_API_KEY:
            return self.settings.OPENAI_MODEL, "openai"
        if self.settings.GEMINI_API_KEY:
            return self.settings.GEMINI_MODEL, "google"

        return self.settings.CLAUDE_MODEL, "anthropic"  # will fail at call time

    def _has_key(self, provider: str) -> bool:
        """判斷 key。"""
        return bool({
            "anthropic": self.settings.ANTHROPIC_API_KEY,
            "openai": self.settings.OPENAI_API_KEY,
            "google": self.settings.GEMINI_API_KEY,
        }.get(provider, ""))

    # ----------------------------------------------------------
    # Model alias resolution
    # ----------------------------------------------------------

    _MODEL_ALIASES = {
        "gemini-flash": "GEMINI_MODEL",
        "gemini-pro": "GEMINI_MODEL",
        "claude-sonnet": "CLAUDE_MODEL",
        "claude-haiku": "CLAUDE_HAIKU_MODEL",
    }

    def _resolve_model_alias(self, model: str) -> str:
        """Resolve shorthand model names (e.g. 'gemini-flash') to full API names."""
        setting_key = self._MODEL_ALIASES.get(model.lower())
        if setting_key:
            return getattr(self.settings, setting_key, model)
        return model

    # ----------------------------------------------------------
    # Unified generation API
    # ----------------------------------------------------------

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        plan: str = "FREE",
        task_type: str = "basic",
        max_tokens: int = 4096,
        feature: str = "llm_generate",
    ) -> str:
        """Generate text using the appropriate LLM.

        If model is specified, uses it directly.
        Otherwise resolves from plan + task_type routing.

        Args:
            feature: Sprint 8 T70 — ai_usage_ledger.feature label，
                供 /admin/cost/by-feature 拆解花費佔比。callsite 應傳入
                具體業務功能（如 "ai_chat" / "ai_question_gen" / "encouragement"
                / "weekly_report" / "wrong_answer_explain"），未傳入則回退
                generic "llm_generate"（不利毛利分析）。
        """
        if model:
            # Resolve shorthand model names to full API model names
            model = self._resolve_model_alias(model)
            provider = _detect_provider(model)
        else:
            model, provider = self.resolve_model(plan, task_type)

        logger.info("LLM generate: model=%s provider=%s feature=%s", model, provider, feature)

        # TODO #4 — auto-track AI usage in ai_usage_ledger when db available
        if self.db is not None:
            return self._generate_with_tracking(
                provider, model, system_prompt, user_prompt, max_tokens, feature
            )

        if provider == "anthropic":
            if self._use_claude_cli():
                return self._generate_claude_cli(model, system_prompt, user_prompt, max_tokens)
            return self._generate_anthropic(model, system_prompt, user_prompt, max_tokens)
        elif provider == "openai":
            return self._generate_openai(model, system_prompt, user_prompt, max_tokens)
        elif provider == "google":
            return self._generate_google(model, system_prompt, user_prompt, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _generate_with_tracking(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        feature: str = "llm_generate",
    ) -> str:
        """Wrap generate() in track_ai_usage for ai_usage_ledger.

        Estimates tokens via char count (~4 chars/token) when provider
        response doesn't expose exact counts.
        """
        from app.middleware.ai_usage_tracker import (
            estimate_anthropic_cost,
            estimate_gemini_cost,
            track_ai_usage,
        )
        # Map provider name to tracker provider (excluding openai which is not budgeted)
        if provider == "anthropic":
            tracker_provider = "anthropic"
        elif provider == "google":
            tracker_provider = "gemini"
        else:
            # openai or unknown — skip tracking (no budget scope)
            if provider == "anthropic":
                if self._use_claude_cli():
                    return self._generate_claude_cli(model, system_prompt, user_prompt, max_tokens)
                return self._generate_anthropic(model, system_prompt, user_prompt, max_tokens)
            elif provider == "openai":
                return self._generate_openai(model, system_prompt, user_prompt, max_tokens)
            elif provider == "google":
                return self._generate_google(model, system_prompt, user_prompt, max_tokens)
            raise ValueError(f"Unknown provider: {provider}")

        with track_ai_usage(
            self.db, provider=tracker_provider, feature=feature
        ) as tracker:
            if provider == "anthropic":
                if self._use_claude_cli():
                    result = self._generate_claude_cli(model, system_prompt, user_prompt, max_tokens)
                else:
                    result = self._generate_anthropic(model, system_prompt, user_prompt, max_tokens)
            else:  # google
                result = self._generate_google(model, system_prompt, user_prompt, max_tokens)

            # Estimate tokens from char counts (~4 chars/token)
            in_tokens = (len(system_prompt) + len(user_prompt)) // 4 or 1
            out_tokens = len(result) // 4 or 1
            tracker.input_tokens = in_tokens
            tracker.output_tokens = out_tokens
            tracker.endpoint = model

            if tracker_provider == "anthropic":
                tracker.cost_usd = estimate_anthropic_cost(
                    in_tokens, out_tokens, model=model
                )
            else:
                tracker.cost_usd = estimate_gemini_cost(
                    in_tokens, out_tokens, model=model
                )

        return result

    def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str,
        model: str | None = None,
        plan: str = "FREE",
        task_type: str = "basic",
        max_tokens: int = 4096,
        feature: str = "rag_with_context",
    ) -> str:
        """Generate with RAG context prepended to user prompt."""
        full_prompt = (
            f"以下是從使用者上傳文件中檢索到的相關段落：\n\n"
            f"---\n{context}\n---\n\n"
            f"{user_prompt}"
        )
        return self.generate(
            system_prompt, full_prompt, model=model,
            plan=plan, task_type=task_type, max_tokens=max_tokens, feature=feature,
        )

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        plan: str = "FREE",
        task_type: str = "basic",
        max_tokens: int = 4096,
        feature: str = "json_generate",
    ) -> dict:
        """Generate and parse JSON response."""
        raw = self.generate(system_prompt, user_prompt, plan=plan, task_type=task_type, max_tokens=max_tokens, feature=feature)
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        return json.loads(text)

    # ----------------------------------------------------------
    # PDF / Image (Claude only, others fallback to text extraction)
    # ----------------------------------------------------------

    def parse_pdf(self, pdf_bytes: bytes, prompt: str) -> str:
        """Parse PDF using Claude's native PDF input (Anthropic only)."""
        import base64
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        client = self._get_anthropic()
        message = client.messages.create(
            model=self.settings.CLAUDE_PDF_MODEL,
            max_tokens=8192,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return message.content[0].text

    def parse_image(self, image_bytes: bytes, media_type: str, prompt: str) -> str:
        """Parse image using Claude Vision (Anthropic only)."""
        import base64
        img_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        client = self._get_anthropic()
        message = client.messages.create(
            model=self.settings.CLAUDE_PDF_MODEL,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return message.content[0].text

    # ----------------------------------------------------------
    # Provider-specific implementations
    # ----------------------------------------------------------

    def _generate_anthropic(self, model: str, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """產生 anthropic。"""
        client = self._get_anthropic()
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    def _generate_openai(self, model: str, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """產生 openai。"""
        client = self._get_openai()
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def _generate_google(self, model: str, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """Generate via Gemini with optional explicit context caching (Tier 1-C).

        Flow:
        1. Attempt to fetch/create a cached-content resource for the system_prompt.
        2. If cache available → send only user_prompt + cached_content reference.
        3. Otherwise → send combined prompt (rely on Gemini implicit caching).
        4. Record cached_content_token_count for observability.
        """
        from app.services.gemini_cache_service import GeminiCacheService

        client = self._get_google()
        cache_svc = GeminiCacheService()

        # Try explicit caching for the system prompt
        cache_name = cache_svc.get_or_create_cache(
            model=model,
            system_prompt=system_prompt,
            display_name=f"llm-{model}-sys",
            ttl_seconds=3600,
        )

        try:
            if cache_name:
                response = client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config={
                        "max_output_tokens": max_tokens,
                        "cached_content": cache_name,
                    },
                )
            else:
                combined_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = client.models.generate_content(
                    model=model,
                    contents=combined_prompt,
                    config={"max_output_tokens": max_tokens},
                )
        except Exception as exc:
            # Graceful fallback: cache reference may have expired server-side
            import logging
            logging.getLogger(__name__).warning(
                "Gemini generate with cache failed (%s); retrying without cache",
                exc,
            )
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = client.models.generate_content(
                model=model,
                contents=combined_prompt,
                config={"max_output_tokens": max_tokens},
            )

        # Track cache savings (implicit + explicit)
        try:
            cached_tokens = (
                getattr(response.usage_metadata, "cached_content_token_count", 0) or 0
            )
            cache_svc.record_cached_tokens_seen(cached_tokens)
        except Exception:  # noqa: BLE001
            pass

        return response.text
