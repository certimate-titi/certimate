"""Resource-specific storage helpers for EPIC-035.

Layered on top of storage_service.py's LocalStorageService / GCSStorageService.

Responsibilities:
  - PDF → WebP 頁縮圖（1200×800，quality=80）
  - 嵌入圖抽取（PyMuPDF）+ 裝飾圖過濾
  - 依用途分 prefix：
      uploads/<user>/originals/<resource>.pdf      → 7d 刪除
      uploads/<user>/thumbnails/<resource>/pN.webp → Lifecycle
      uploads/<user>/figures/<resource>/pN_iM.png  → Lifecycle
      critical/<user>/<resource>/pN.webp           → 永久 Standard
"""

from __future__ import annotations

import io
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

WEBP_MAX_W = 1200
WEBP_MAX_H = 1600
WEBP_QUALITY = 80
MIN_FIGURE_BYTES = 2048  # 過濾裝飾（< 2KB 視為 icon/logo）


@dataclass
class PageRenderResult:
    page_no: int
    webp_path: str           # storage path (gs:// or local)
    figures: list[str]       # embedded figure storage paths


def _pil_to_webp_bytes(pil_img) -> bytes:
    buf = io.BytesIO()
    pil_img.thumbnail((WEBP_MAX_W, WEBP_MAX_H))
    pil_img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=6)
    return buf.getvalue()


def render_pdf_to_webp(
    pdf_path: str,
    user_id: str,
    resource_id: str,
    critical_pages: set[int] | None = None,
) -> list[PageRenderResult]:
    """將 PDF 每頁轉 WebP 縮圖 + 抽取嵌入圖。

    critical_pages 中的頁面改走 critical/<user>/... 路徑（不套 lifecycle）。
    非關鍵頁走 uploads/<user>/thumbnails/...

    回傳 per-page PageRenderResult。
    """
    try:
        import fitz  # PyMuPDF
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "PyMuPDF + Pillow required for resource rendering"
        ) from e

    critical_pages = critical_pages or set()
    storage = get_storage_service()
    results: list[PageRenderResult] = []

    doc = fitz.open(pdf_path)
    try:
        for page_no in range(len(doc)):
            page = doc[page_no]

            # render full page → WebP
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            webp_bytes = _pil_to_webp_bytes(img)

            # 分 prefix：critical 永久 Standard / 否則 uploads/
            if (page_no + 1) in critical_pages:
                key_prefix = f"critical/{user_id}/{resource_id}"
            else:
                key_prefix = f"thumbnails/{user_id}/{resource_id}"

            webp_path = storage.save_file(
                user_id=user_id,
                resource_id=resource_id,
                filename=f"{key_prefix}/p{page_no + 1}.webp",
                data=webp_bytes,
            )

            # 嵌入圖抽取
            figure_paths: list[str] = []
            for img_idx, img_info in enumerate(page.get_images(full=True)):
                xref = img_info[0]
                try:
                    base_img = doc.extract_image(xref)
                    raw = base_img["image"]
                    if len(raw) < MIN_FIGURE_BYTES:
                        continue  # 過濾裝飾
                    ext = base_img.get("ext", "png")
                    fig_filename = (
                        f"figures/{user_id}/{resource_id}"
                        f"/p{page_no + 1}_i{img_idx}.{ext}"
                    )
                    fig_path = storage.save_file(
                        user_id=user_id,
                        resource_id=resource_id,
                        filename=fig_filename,
                        data=raw,
                    )
                    figure_paths.append(fig_path)
                except Exception:
                    logger.warning(
                        "figure extract failed resource=%s page=%d idx=%d",
                        resource_id, page_no, img_idx, exc_info=True,
                    )

            results.append(
                PageRenderResult(
                    page_no=page_no + 1,
                    webp_path=webp_path,
                    figures=figure_paths,
                )
            )
    finally:
        doc.close()

    logger.info(
        "rendered resource=%s pages=%d critical=%d",
        resource_id, len(results), len(critical_pages),
    )
    return results


def delete_original_pdf(storage_path: str) -> None:
    """解析成功後刪除原始 PDF（§9 原始 PDF 保 7 天由 lifecycle 兜底）。

    若要立即刪除可呼叫此函式；預設讓 lifecycle 刪除以容錯重跑。
    """
    storage = get_storage_service()
    try:
        storage.delete_file(storage_path)
    except Exception:
        logger.warning("original pdf delete failed: %s", storage_path, exc_info=True)
