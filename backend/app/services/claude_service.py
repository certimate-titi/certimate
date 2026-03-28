"""ClaudeService — Anthropic Claude API wrapper."""

import json
import anthropic

from app.core.config import get_settings


class ClaudeService:
    """Thin wrapper around the Anthropic Claude API."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.pdf_model = settings.CLAUDE_PDF_MODEL

    def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a response using RAG context.

        The context is injected as a separate section before the user prompt.
        """
        full_user_prompt = (
            f"以下是從使用者上傳文件中檢索到的相關段落：\n\n"
            f"---\n{context}\n---\n\n"
            f"{user_prompt}"
        )
        return self.generate_simple(system_prompt, full_user_prompt, max_tokens)

    def generate_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a response without RAG context."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    def parse_pdf(self, pdf_bytes: bytes, prompt: str) -> str:
        """Send a PDF to Claude for parsing using native PDF support.

        Returns the text response from Claude.
        """
        import base64
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        message = self.client.messages.create(
            model=self.pdf_model,
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )
        return message.content[0].text

    def parse_image(self, image_bytes: bytes, media_type: str, prompt: str) -> str:
        """Send an image to Claude Vision for OCR."""
        import base64
        img_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        message = self.client.messages.create(
            model=self.pdf_model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )
        return message.content[0].text

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> dict:
        """Generate and parse a JSON response from Claude."""
        raw = self.generate_simple(system_prompt, user_prompt, max_tokens)
        # Extract JSON from response (may be wrapped in ```json ... ```)
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last line (```json and ```)
            text = "\n".join(lines[1:-1])
        return json.loads(text)
