"""分片上傳 Service — ULTRA 方案專屬。

支援大檔案斷點續傳：
1. 初始化上傳 → 取得 upload_id + chunk_size + total_chunks
2. 上傳各分片（可斷點續傳）
3. 所有分片上傳完成後合併
"""

import os
import uuid
import hashlib
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.user import User, SubscriptionPlan
from app.models.plan_quota import PlanQuota

logger = logging.getLogger("certimate.chunked_upload")

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "chunks"
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB per chunk
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB max for ULTRA

# Plan name display mapping
PLAN_DB_TO_DISPLAY = {
    "FREE": "FREE",
    "PRO": "PRO_199",
    "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599",
    "EDU": "EDU",
}

# In-memory registry (production would use Redis)
_uploads: dict[str, dict] = {}


class ChunkedUploadService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_ultra(self, user_id: str, file_size: int = 0) -> dict | User:
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        plan_display = PLAN_DB_TO_DISPLAY.get(plan, plan)

        if plan != "ULTRA":
            # Check plan file size limit
            quota = self.db.query(PlanQuota).filter_by(plan=plan_display).first()
            if not quota:
                quota = self.db.query(PlanQuota).filter_by(plan=plan).first()
            max_mb = quota.max_file_size_mb if quota and quota.max_file_size_mb else 100
            file_size_mb = file_size / (1024 * 1024) if file_size else 0
            if file_size_mb > max_mb:
                return {
                    "error": True,
                    "status_code": 400,
                    "message": f"檔案大小超過 {plan_display} 方案限制（{max_mb}MB）",
                }
            return {"error": True, "status_code": 403, "message": "分片上傳僅限 ULTRA 方案使用"}

        return user

    def init_upload(self, user_id: str, filename: str, file_size: int, subject_id: str = None) -> dict:
        """初始化分片上傳。"""
        result = self._validate_ultra(user_id, file_size)
        if isinstance(result, dict):
            return result

        if file_size > MAX_FILE_SIZE:
            return {"error": True, "status_code": 400, "message": f"檔案大小超過限制（最大 {MAX_FILE_SIZE // (1024*1024)} MB）"}

        upload_id = str(uuid.uuid4())
        total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

        # 建立分片暫存目錄
        chunk_dir = UPLOAD_DIR / upload_id
        chunk_dir.mkdir(parents=True, exist_ok=True)

        _uploads[upload_id] = {
            "user_id": user_id,
            "filename": filename,
            "file_size": file_size,
            "total_chunks": total_chunks,
            "uploaded_chunks": set(),
            "chunk_dir": str(chunk_dir),
            "subject_id": subject_id,
        }

        return {
            "upload_id": upload_id,
            "chunk_size": CHUNK_SIZE,
            "total_chunks": total_chunks,
        }

    def upload_chunk(self, user_id: str, upload_id: str, chunk_index: int, chunk_data: bytes) -> dict:
        """上傳單一分片。"""
        if upload_id not in _uploads:
            return {"error": True, "status_code": 404, "message": "上傳任務不存在或已過期"}

        upload_info = _uploads[upload_id]
        if upload_info["user_id"] != user_id:
            return {"error": True, "status_code": 403, "message": "無權操作此上傳任務"}

        if chunk_index < 0 or chunk_index >= upload_info["total_chunks"]:
            return {"error": True, "status_code": 400, "message": f"分片索引超出範圍（0-{upload_info['total_chunks']-1}）"}

        # 寫入分片
        chunk_path = Path(upload_info["chunk_dir"]) / f"chunk_{chunk_index:05d}"
        chunk_path.write_bytes(chunk_data)
        upload_info["uploaded_chunks"].add(chunk_index)

        remaining = upload_info["total_chunks"] - len(upload_info["uploaded_chunks"])

        return {
            "chunk_index": chunk_index,
            "uploaded": True,
            "total_uploaded": len(upload_info["uploaded_chunks"]),
            "total_chunks": upload_info["total_chunks"],
            "remaining": remaining,
        }

    def get_upload_status(self, user_id: str, upload_id: str) -> dict:
        """查詢上傳狀態（用於斷點續傳）。"""
        if upload_id not in _uploads:
            return {"error": True, "status_code": 404, "message": "上傳任務不存在或已過期"}

        upload_info = _uploads[upload_id]
        if upload_info["user_id"] != user_id:
            return {"error": True, "status_code": 403, "message": "無權操作此上傳任務"}

        uploaded = len(upload_info["uploaded_chunks"])
        total = upload_info["total_chunks"]
        complete = uploaded == total
        status = "completed" if complete else "in_progress"

        # Find next chunk to upload (1-indexed for display)
        missing = sorted(set(range(total)) - upload_info["uploaded_chunks"])
        next_chunk_index_0 = missing[0] if missing else total
        next_chunk_1based = next_chunk_index_0 + 1

        return {
            "upload_id": upload_id,
            "filename": upload_info["filename"],
            "total_chunks": total,
            "uploaded_chunks": uploaded,
            "status": status,
            "next_chunk_index": next_chunk_1based,
            "next_chunk": next_chunk_1based,
            "missing_chunks": missing,
            "complete": complete,
        }

    def merge_chunks(self, user_id: str, upload_id: str) -> dict:
        """合併所有分片為完整檔案。"""
        if upload_id not in _uploads:
            return {"error": True, "status_code": 404, "message": "上傳任務不存在或已過期"}

        upload_info = _uploads[upload_id]
        if upload_info["user_id"] != user_id:
            return {"error": True, "status_code": 403, "message": "無權操作此上傳任務"}

        if len(upload_info["uploaded_chunks"]) != upload_info["total_chunks"]:
            missing = sorted(set(range(upload_info["total_chunks"])) - upload_info["uploaded_chunks"])
            return {"error": True, "status_code": 400, "message": f"尚有 {len(missing)} 個分片未上傳"}

        file_size = upload_info["file_size"]

        # Create a resource record in DB
        from app.models.resource import Resource, ResourceType, ResourceStatus
        resource = Resource(
            user_id=uuid.UUID(upload_info["user_id"]),
            name=upload_info["filename"],
            type=ResourceType.PDF,
            status=ResourceStatus.PENDING,
            file_size_bytes=file_size,
            subject_id=uuid.UUID(upload_info["subject_id"]) if upload_info.get("subject_id") else None,
        )
        self.db.add(resource)
        self.db.flush()
        self.db.refresh(resource)

        # 合併分片並存入 Storage Service
        from app.services.storage_service import get_storage_service
        storage = get_storage_service()
        chunk_dir = Path(upload_info["chunk_dir"])
        merged_data = bytearray()
        for i in range(upload_info["total_chunks"]):
            chunk_path = chunk_dir / f"chunk_{i:05d}"
            merged_data.extend(chunk_path.read_bytes())

        storage_path = storage.save_file(
            user_id=upload_info["user_id"],
            resource_id=str(resource.id),
            filename=upload_info["filename"],
            data=bytes(merged_data),
        )
        resource.gcs_path = storage_path
        self.db.commit()

        # 清理本地暫存分片
        import shutil
        if chunk_dir.exists():
            shutil.rmtree(chunk_dir, ignore_errors=True)

        # Clean up in-memory state
        del _uploads[upload_id]

        return {
            "merged": True,
            "resource_id": str(resource.id),
            "status": "PENDING",
            "file_size_bytes": file_size,
            "gcs_path": storage_path,
            "resource": {
                "id": str(resource.id),
                "status": "PENDING",
                "file_size_bytes": file_size,
            },
        }
