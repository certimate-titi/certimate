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
        self.db = db
        self.settings = get_settings()
        self._clients: dict = {}

    # ----------------------------------------------------------
    # Client lazy initialization
    # ----------------------------------------------------------

    def _get_anthropic(self):
        if "anthropic" not in self._clients:
            import anthropic
            self._clients["anthropic"] = anthropic.Anthropic(
                api_key=self.settings.ANTHROPIC_API_KEY
            )
        return self._clients["anthropic"]

    def _get_openai(self):
        if "openai" not in self._clients:
            import openai
            self._clients["openai"] = openai.OpenAI(
                api_key=self.settings.OPENAI_API_KEY
            )
        return self._clients["openai"]

    def _get_google(self):
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
    ) -> str:
        """Generate text using the appropriate LLM.

        If model is specified, uses it directly.
        Otherwise resolves from plan + task_type routing.
        """
        if model:
            # Resolve shorthand model names to full API model names
            model = self._resolve_model_alias(model)
            provider = _detect_provider(model)
        else:
            model, provider = self.resolve_model(plan, task_type)

        logger.info("LLM generate: model=%s provider=%s", model, provider)

        if provider == "anthropic":
            return self._generate_anthropic(model, system_prompt, user_prompt, max_tokens)
        elif provider == "openai":
            return self._generate_openai(model, system_prompt, user_prompt, max_tokens)
        elif provider == "google":
            return self._generate_google(model, system_prompt, user_prompt, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str,
        plan: str = "FREE",
        task_type: str = "basic",
        max_tokens: int = 4096,
    ) -> str:
        """Generate with RAG context prepended to user prompt."""
        full_prompt = (
            f"以下是從使用者上傳文件中檢索到的相關段落：\n\n"
            f"---\n{context}\n---\n\n"
            f"{user_prompt}"
        )
        return self.generate(system_prompt, full_prompt, plan=plan, task_type=task_type, max_tokens=max_tokens)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        plan: str = "FREE",
        task_type: str = "basic",
        max_tokens: int = 4096,
    ) -> dict:
        """Generate and parse JSON response."""
        raw = self.generate(system_prompt, user_prompt, plan=plan, task_type=task_type, max_tokens=max_tokens)
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
        client = self._get_anthropic()
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    def _generate_openai(self, model: str, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
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
        client = self._get_google()
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = client.models.generate_content(
            model=model,
            contents=combined_prompt,
            config={"max_output_tokens": max_tokens},
        )
        return response.text
