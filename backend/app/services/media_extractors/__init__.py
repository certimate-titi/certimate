"""Media Extractors — Layer 1 of the unified resource processing pipeline.

Each extractor takes a file path and returns:
    {
        "title": str,
        "content_type": str,   # pdf|docx|pptx|xlsx|doc|ppt|xls|image_ocr|transcript
        "raw_text": str,       # 提取的原始文字
        "metadata": str,       # 來源元資料（頁碼/sheet名稱/時間戳等）
        "sections": list[dict] # optional pre-split sections
    }

LLM is NOT used in this layer — pure engineering extraction only.
"""

from app.services.media_extractors.registry import extract, get_extractor

__all__ = ["extract", "get_extractor"]
