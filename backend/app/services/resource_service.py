"""Resource service — business logic for resource upload."""

import re

from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope
from app.repositories.resource_repository import ResourceRepository
from app.repositories.user_repository import UserRepository


ALLOWED_EXTENSIONS = {"pdf", "md", "markdown", "txt", "png", "jpg", "jpeg", "gif", "bmp", "webp"}

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

YOUTUBE_REGEX = re.compile(r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]+")

FILE_SIZE_LIMITS_MB = {
    "FREE": 10,
    "PRO": 100,
    "PRO_PLUS": 100,
    "ULTRA": 500,
}

VISION_OCR_MIN_PLAN = ["PRO_PLUS", "ULTRA"]


def _get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _get_plan_value(plan) -> str:
    return plan.value if hasattr(plan, "value") else plan


class ResourceService:

    def __init__(self, resource_repo: ResourceRepository, user_repo: UserRepository):
        self.resource_repo = resource_repo
        self.user_repo = user_repo

    def upload(self, user_id: str, filename: str, subject_id: str,
               file_size_mb: int = None, resource_type: str = None) -> dict:
        if not filename or not subject_id:
            return {"error": True, "status_code": 400, "message": "必要參數未提供"}

        ext = _get_extension(filename)
        if ext not in ALLOWED_EXTENSIONS:
            return {
                "error": True, "status_code": 400,
                "message": "不支援的檔案格式，請上傳 PDF、Markdown 或通用圖片檔案",
            }

        user = self.user_repo.find_by_id(user_id)
        if user is None:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = _get_plan_value(user.subscription_plan)

        # Check if image upload requires PRO_PLUS or above
        is_image = ext in IMAGE_EXTENSIONS or resource_type == "image"
        if is_image and plan not in VISION_OCR_MIN_PLAN:
            return {
                "error": True, "status_code": 400,
                "message": "手寫圖片辨識（Vision OCR）需升級至 PRO_PLUS 方案",
            }

        # Check file size limit
        if file_size_mb is not None:
            limit = FILE_SIZE_LIMITS_MB.get(plan, 10)
            if file_size_mb > limit:
                return {
                    "error": True, "status_code": 400,
                    "message": f"檔案大小超過 {plan} 方案限制（{limit}MB）",
                }

        # Determine resource type
        if resource_type:
            r_type = resource_type
        elif is_image:
            r_type = "image"
        elif ext in ("md", "markdown"):
            r_type = "markdown"
        elif ext == "txt":
            r_type = "txt"
        else:
            r_type = "pdf"

        # Determine processing engine
        processing_engine = "gemini_flash"
        if is_image:
            processing_engine = "vision_ocr"

        resource = Resource(
            user_id=user_id,
            subject_id=subject_id,
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

    def submit_youtube(self, user_id: str, youtube_url: str, subject_id: str) -> dict:
        if not subject_id:
            return {"error": True, "status_code": 400, "message": "必要參數未提供"}

        if not YOUTUBE_REGEX.match(youtube_url):
            return {"error": True, "status_code": 400, "message": "無效的 YouTube URL"}

        resource = Resource(
            user_id=user_id,
            subject_id=subject_id,
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
