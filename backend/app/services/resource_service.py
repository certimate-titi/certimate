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

YOUTUBE_REGEX = re.compile(r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]+")

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
        r_type = resource_type or EXTENSION_TO_RESOURCE_TYPE.get(ext, "pdf")
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

        if not YOUTUBE_REGEX.match(youtube_url):
            return {"error": True, "status_code": 400, "message": "無效的 YouTube URL"}

        from app.core.deps import PUBLIC_B2C_TENANT_ID
        resource = Resource(
            user_id=user_id,
            subject_id=subject_id,
            tenant_id=tenant_id or PUBLIC_B2C_TENANT_ID,
            name=youtube_url,
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
