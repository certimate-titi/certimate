"""ClaudeService — backward-compatible wrapper around LLMService.

Delegates all calls to LLMService for multi-provider routing.
Existing code that imports ClaudeService continues to work unchanged.
"""

from app.services.llm_service import LLMService


class ClaudeService:
    """Thin backward-compatible wrapper.

    All new code should use LLMService directly.
    """

    def __init__(self, db=None):
        """初始化實例。"""
        self._llm = LLMService(db=db)

    def generate_with_context(self, system_prompt, user_prompt, context, max_tokens=4096):
        """產生 with context。"""
        return self._llm.generate_with_context(system_prompt, user_prompt, context, max_tokens=max_tokens)

    def generate_simple(self, system_prompt, user_prompt, max_tokens=4096):
        """產生 simple。"""
        return self._llm.generate(system_prompt, user_prompt, max_tokens=max_tokens)

    def parse_pdf(self, pdf_bytes, prompt):
        """解析 pdf。"""
        return self._llm.parse_pdf(pdf_bytes, prompt)

    def parse_image(self, image_bytes, media_type, prompt):
        """解析 image。"""
        return self._llm.parse_image(image_bytes, media_type, prompt)

    def generate_json(self, system_prompt, user_prompt, max_tokens=4096):
        """產生 json。"""
        return self._llm.generate_json(system_prompt, user_prompt, max_tokens=max_tokens)
