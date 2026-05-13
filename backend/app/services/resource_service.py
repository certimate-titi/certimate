"""Resource service — business logic for resource upload."""

import re

from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope, FILE_SIZE_LIMITS
from app.repositories.resource_repository import ResourceRepository
from app.repositories.user_repository import UserRepository


ALLOWED_EXTENSIONS = {
    # Documents
    "pdf", "md", "markdown", "txt",
    "docx", "pptx", "xlsx",
    "doc", "ppt", "xls",
    # Images
    "png", "jpg", "jpeg", "gif", "bmp", "webp",
    # Audio
    "mp3", "wav", "m4a", "flac", "ogg", "wma", "aac",
    # Video
    "mp4", "mov", "avi", "mkv", "webm", "wmv", "flv",
}

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

DOCUMENT_EXTENSIONS = {"pdf", "docx", "pptx", "xlsx", "doc", "ppt", "xls", "md", "markdown", "txt"}

AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "flac", "ogg", "wma", "aac"}

VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "wmv", "flv"}

# Extension → ResourceType mapping
EXTENSION_TO_RESOURCE_TYPE = {
    "pdf": "pdf", "md": "markdown", "markdown": "markdown", "txt": "txt",
    "docx": "docx", "pptx": "pptx", "xlsx": "xlsx",
    "doc": "doc", "ppt": "ppt", "xls": "xls",
    "png": "image", "jpg": "image", "jpeg": "image",
    "gif": "image", "bmp": "image", "webp": "image",
    "mp3": "audio", "wav": "audio", "m4a": "audio",
    "flac": "audio", "ogg": "audio", "wma": "audio", "aac": "audio",
    "mp4": "video", "mov": "video", "avi": "video",
    "mkv": "video", "webm": "video", "wmv": "video", "flv": "video",
}

YOUTUBE_REGEX = re.compile(
    r"^https?://(?:(?:www\.)?youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)[\w-]+"
)

YOUTUBE_OEMBED_URL = "https://www.youtube.com/oembed?url={url}&format=json"


def _fetch_youtube_title_oembed(youtube_url: str) -> str | None:
    """P0-2：透過 YouTube oEmbed endpoint 取得影片 title。

    oEmbed 無需 API 金鑰，不觸發 bot challenge，回傳 title / author_name。
    失敗時 return None（由呼叫方決定 fallback）。

    Endpoint: https://www.youtube.com/oembed?url={url}&format=json
    """
    import logging
    import urllib.request
    import urllib.error
    import json

    logger = logging.getLogger(__name__)
    try:
        api_url = YOUTUBE_OEMBED_URL.format(url=youtube_url)
        req = urllib.request.Request(api_url, headers={"User-Agent": "certimate/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("title") or None
    except Exception as exc:
        logger.warning("oEmbed fetch failed for %s: %s", youtube_url, exc)
        return None

FILE_SIZE_LIMITS_MB = {
    "FREE": 10,
    "PRO": 100,
    "PRO_PLUS": 100,
    "ULTRA": 500,
}

PLAN_DISPLAY_NAME = {
    "FREE": "FREE",
    "PRO": "PRO_199",
    "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599",
}

VISION_OCR_MIN_PLAN = ["PRO_PLUS", "ULTRA"]


def _get_extension(filename: str) -> str:
    """取得 extension。"""
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _get_plan_value(plan) -> str:
    """取得 plan value。"""
    return plan.value if hasattr(plan, "value") else plan


class ResourceService:

    """Resource Service 服務類別。"""
    def __init__(self, resource_repo: ResourceRepository, user_repo: UserRepository):
        """初始化實例。"""
        self.resource_repo = resource_repo
        self.user_repo = user_repo

    def upload(self, user_id: str, filename: str, subject_id: str,
               file_size_mb: int = None, resource_type: str = None,
               tenant_id: str = None) -> dict:
        """upload。"""
        if not filename or not subject_id:
            return {"error": True, "status_code": 400, "message": "必要參數未提供"}

        ext = _get_extension(filename)
        if ext not in ALLOWED_EXTENSIONS:
            supported = "PDF、DOCX、PPTX、XLSX、DOC、PPT、XLS、Markdown、圖片、音訊（MP3/WAV/M4A）、影片（MP4/MOV）"
            return {
                "error": True, "status_code": 400,
                "message": f"不支援的檔案格式，支援的格式：{supported}",
            }

        user = self.user_repo.find_by_id(user_id)
        if user is None:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = _get_plan_value(user.subscription_plan)

        # Determine resource type from extension
        # RC4 修補（2026-04-29）：傳入的 resource_type 必須 normalize 為小寫
        # PostgreSQL enum resource_type 只接受小寫 value，前端傳 "PDF" 會直接 raise
        # InvalidTextRepresentation。空字串 / None 退回副檔名映射。
        _input_type = (resource_type or "").strip().lower()
        r_type = _input_type or EXTENSION_TO_RESOURCE_TYPE.get(ext, "pdf")
        # 白名單驗證：只接受 EXTENSION_TO_RESOURCE_TYPE 的 value 集合
        _valid_types = set(EXTENSION_TO_RESOURCE_TYPE.values())
        if r_type not in _valid_types:
            return {
                "error": True, "status_code": 400,
                "message": f"不支援的 resource_type: {resource_type!r}（合法：{sorted(_valid_types)}）",
            }
        is_image = ext in IMAGE_EXTENSIONS or r_type == "image"

        # Check if image upload requires PRO_PLUS or above
        if is_image and plan not in VISION_OCR_MIN_PLAN:
            return {
                "error": True, "status_code": 400,
                "message": "手寫圖片辨識（Vision OCR）需升級至 PRO_PLUS 方案",
            }

        # Check file size limit (plan-based)
        if file_size_mb is not None:
            limit = FILE_SIZE_LIMITS_MB.get(plan, 10)
            if file_size_mb > limit:
                display_name = PLAN_DISPLAY_NAME.get(plan, plan)
                return {
                    "error": True, "status_code": 400,
                    "message": f"檔案大小超過 {display_name} 方案限制（{limit}MB）",
                }

        # Check file size limit (type-based)
        if file_size_mb is not None:
            type_limit_bytes = FILE_SIZE_LIMITS.get(r_type, 50 * 1024 * 1024)
            type_limit_mb = type_limit_bytes / (1024 * 1024)
            if file_size_mb > type_limit_mb:
                return {
                    "error": True, "status_code": 400,
                    "message": f"檔案大小超過{r_type}類型限制（{int(type_limit_mb)}MB）",
                }

        # Determine processing engine
        if is_image:
            processing_engine = "vision_ocr"
        elif r_type in ("audio", "video"):
            processing_engine = "whisper_api"
        else:
            processing_engine = "gemini_flash"

        from app.core.deps import PUBLIC_B2C_TENANT_ID
        resource = Resource(
            user_id=user_id,
            subject_id=subject_id,
            tenant_id=tenant_id or PUBLIC_B2C_TENANT_ID,
            name=filename,
            type=r_type,
            scope=ResourceScope.PERSONAL,
            status=ResourceStatus.PENDING,
            file_size_bytes=(file_size_mb * 1024 * 1024) if file_size_mb else None,
            processing_engine=processing_engine,
            implicit_consent=True,
        )
        saved = self.resource_repo.save(resource)

        return {
            "error": False,
            "id": str(saved.id),
            "name": saved.name,
            "type": r_type,
            "status": "PENDING",
            "processing_engine": processing_engine,
            "implicit_consent": True,
        }

    def submit_youtube(self, user_id: str, youtube_url: str, subject_id: str,
                       tenant_id: str = None) -> dict:
        """submit youtube。"""
        if not subject_id:
            return {"error": True, "status_code": 400, "message": "必要參數未提供"}

        # SSRF + YouTube 格式檢查：分階段處理避免訊息錯誤
        #   1. 若 URL hostname 是 IP 字面量（含 cloud metadata 域名）→ SSRF 先檢查（具體訊息）
        #   2. 否則按 YouTube 格式 regex 檢查 → 不符即「無效的 YouTube URL」
        #   3. 通過 regex 才跑完整 SSRF（防 DNS rebinding 到內網）
        from urllib.parse import urlparse
        from app.core.security import (
            validate_url_for_ssrf, SSRFError, _BLOCKED_HOSTNAMES, _check_host_ip,
        )
        import ipaddress as _ipaddr

        parsed = urlparse(youtube_url)
        host = (parsed.hostname or "").lower().rstrip(".")
        is_ip_literal = False
        try:
            _ipaddr.ip_address(host)
            is_ip_literal = True
        except ValueError:
            pass

        if host in _BLOCKED_HOSTNAMES:
            return {
                "error": True, "status_code": 422,
                "message": f"URL 指向受保護的內部服務: {host!r}",
            }
        if is_ip_literal:
            try:
                _check_host_ip(host)
            except SSRFError as exc:
                return {"error": True, "status_code": 422, "message": str(exc)}

        if not YOUTUBE_REGEX.match(youtube_url):
            return {"error": True, "status_code": 422, "message": "無效的 YouTube URL（不是有效的 YouTube URL 格式）"}

        try:
            validate_url_for_ssrf(youtube_url)
        except SSRFError as exc:
            return {"error": True, "status_code": 422, "message": str(exc)}
        except ValueError as exc:
            return {"error": True, "status_code": 422, "message": f"不是有效的 YouTube URL: {exc}"}

        from app.core.deps import PUBLIC_B2C_TENANT_ID

        # P0-2：用 oEmbed 取 title 當 resource name，避免 yt-dlp bot challenge。
        # oEmbed 是輕量無認證 endpoint，失敗時 fallback 到 URL。
        resource_name = _fetch_youtube_title_oembed(youtube_url) or youtube_url

        resource = Resource(
            user_id=user_id,
            subject_id=subject_id,
            tenant_id=tenant_id or PUBLIC_B2C_TENANT_ID,
            name=resource_name,
            type="youtube",
            scope=ResourceScope.PERSONAL,
            status=ResourceStatus.PENDING,
            youtube_url=youtube_url,
            processing_engine="gemini_flash",
            implicit_consent=True,
        )
        saved = self.resource_repo.save(resource)

        return {
            "error": False,
            "id": str(saved.id),
            "name": saved.name,
            "type": "youtube",
            "status": "PENDING",
            "processing_engine": "gemini_flash",
            "implicit_consent": True,
        }
