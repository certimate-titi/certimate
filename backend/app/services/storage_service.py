"""Storage Service — 檔案儲存抽象層。

本地開發與雲端部署使用相同介面，差異只在配置：
- STORAGE_BACKEND=local → 存到 uploads/ 目錄（本地開發）
- STORAGE_BACKEND=gcs   → 存到 Google Cloud Storage（雲端部署）

所有路徑統一格式：
- 本地：uploads/{user_id}/{resource_id}/{filename}
- GCS ：gs://{bucket}/{user_id}/{resource_id}/{filename}
"""

import logging
import os
import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseStorageService(ABC):
    """儲存服務抽象基底。"""

    @abstractmethod
    def save_file(self, user_id: str, resource_id: str, filename: str, data: bytes) -> str:
        """儲存檔案，回傳儲存路徑（gcs_path）。"""

    @abstractmethod
    def get_file(self, storage_path: str) -> bytes:
        """讀取檔案內容。"""

    @abstractmethod
    def download_to_temp(self, storage_path: str) -> str:
        """下載檔案到本地暫存目錄，回傳本地路徑。Cloud Run 用 /tmp。"""

    @abstractmethod
    def delete_file(self, storage_path: str) -> None:
        """刪除檔案。"""

    @abstractmethod
    def exists(self, storage_path: str) -> bool:
        """檢查檔案是否存在。"""

    @abstractmethod
    def copy_file(
        self, src_path: str, dst_user_id: str, dst_resource_id: str, dst_filename: str
    ) -> str:
        """將 src_path 複製到新的 (user_id, resource_id, filename)，回傳新路徑。"""


class LocalStorageService(BaseStorageService):
    """本地檔案系統儲存（開發環境）。"""

    def __init__(self, base_dir: str = None):
        """初始化實例。"""
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent.parent / "uploads"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, user_id: str, resource_id: str, filename: str, data: bytes) -> str:
        """儲存 file。"""
        file_dir = self.base_dir / user_id / resource_id
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / filename
        file_path.write_bytes(data)
        logger.info("Local storage: saved %s (%d bytes)", file_path, len(data))
        return str(file_path)

    def get_file(self, storage_path: str) -> bytes:
        """取得 file。"""
        return Path(storage_path).read_bytes()

    def download_to_temp(self, storage_path: str) -> str:
        """本地模式：檔案已在磁碟上，直接回傳路徑。"""
        if Path(storage_path).exists():
            return storage_path
        raise FileNotFoundError(f"檔案不存在: {storage_path}")

    def delete_file(self, storage_path: str) -> None:
        """刪除 file。"""
        path = Path(storage_path)
        if path.exists():
            path.unlink()
            logger.info("Local storage: deleted %s", storage_path)
            # 清理空目錄
            parent = path.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()

    def exists(self, storage_path: str) -> bool:
        """exists。"""
        return Path(storage_path).exists()

    def copy_file(
        self, src_path: str, dst_user_id: str, dst_resource_id: str, dst_filename: str
    ) -> str:
        """copy file。"""
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(f"來源檔案不存在: {src_path}")
        dst_dir = self.base_dir / dst_user_id / dst_resource_id
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_path = dst_dir / dst_filename
        shutil.copy2(src, dst_path)
        logger.info("Local storage: copied %s -> %s", src_path, dst_path)
        return str(dst_path)


class GCSStorageService(BaseStorageService):
    """Google Cloud Storage 儲存（雲端環境）。

    需要安裝 google-cloud-storage 套件。
    """

    def __init__(self, bucket_name: str = None):
        """初始化實例。"""
        self.bucket_name = bucket_name or os.environ.get("GCS_BUCKET", "certimate-uploads")
        self._client = None
        self._bucket = None

    def _get_bucket(self):
        """取得 bucket。"""
        if self._bucket is None:
            from google.cloud import storage
            self._client = storage.Client()
            self._bucket = self._client.bucket(self.bucket_name)
        return self._bucket

    def _build_gcs_key(self, user_id: str, resource_id: str, filename: str) -> str:
        # PRD-033 §3.1：storage key 加 uploads/ 前綴，對應四態 scope 目錄規劃
        """建立 gcs key。"""
        return f"uploads/{user_id}/{resource_id}/{filename}"

    def save_file(self, user_id: str, resource_id: str, filename: str, data: bytes) -> str:
        """儲存 file。"""
        bucket = self._get_bucket()
        key = self._build_gcs_key(user_id, resource_id, filename)
        blob = bucket.blob(key)
        blob.upload_from_string(data)
        gcs_path = f"gs://{self.bucket_name}/{key}"
        logger.info("GCS storage: saved %s (%d bytes)", gcs_path, len(data))
        return gcs_path

    def get_file(self, storage_path: str) -> bytes:
        """取得 file。"""
        bucket = self._get_bucket()
        key = self._parse_gcs_path(storage_path)
        blob = bucket.blob(key)
        return blob.download_as_bytes()

    def download_to_temp(self, storage_path: str) -> str:
        """從 GCS 下載到 /tmp（Cloud Run 的可寫目錄）。"""
        import tempfile
        data = self.get_file(storage_path)
        key = self._parse_gcs_path(storage_path)
        filename = key.split("/")[-1]
        suffix = Path(filename).suffix
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="certimate_")
        os.write(tmp_fd, data)
        os.close(tmp_fd)
        logger.info("GCS storage: downloaded %s to %s", storage_path, tmp_path)
        return tmp_path

    def delete_file(self, storage_path: str) -> None:
        """刪除 file。"""
        bucket = self._get_bucket()
        key = self._parse_gcs_path(storage_path)
        blob = bucket.blob(key)
        if blob.exists():
            blob.delete()
            logger.info("GCS storage: deleted %s", storage_path)

    def exists(self, storage_path: str) -> bool:
        """exists。"""
        bucket = self._get_bucket()
        key = self._parse_gcs_path(storage_path)
        return bucket.blob(key).exists()

    def copy_file(
        self, src_path: str, dst_user_id: str, dst_resource_id: str, dst_filename: str
    ) -> str:
        """copy file。"""
        bucket = self._get_bucket()
        src_key = self._parse_gcs_path(src_path)
        src_blob = bucket.blob(src_key)
        if not src_blob.exists():
            raise FileNotFoundError(f"來源 GCS blob 不存在: {src_path}")
        dst_key = self._build_gcs_key(dst_user_id, dst_resource_id, dst_filename)
        bucket.copy_blob(src_blob, bucket, dst_key)
        dst_path = f"gs://{self.bucket_name}/{dst_key}"
        logger.info("GCS storage: copied %s -> %s", src_path, dst_path)
        return dst_path

    def _parse_gcs_path(self, gcs_path: str) -> str:
        """將 gs://bucket/key 轉為 key。"""
        if gcs_path.startswith("gs://"):
            parts = gcs_path[5:].split("/", 1)
            return parts[1] if len(parts) > 1 else ""
        return gcs_path


def get_storage_service() -> BaseStorageService:
    """根據環境變數取得 Storage Service 實例。

    STORAGE_BACKEND=local（預設）→ LocalStorageService
    STORAGE_BACKEND=gcs         → GCSStorageService
    """
    backend = os.environ.get("STORAGE_BACKEND", "local").lower()
    if backend == "gcs":
        return GCSStorageService()
    return LocalStorageService()


def upload_feedback_attachment(
    file_bytes: bytes,
    filename: str,
    content_type: str = "image/png",
) -> str | None:
    """Upload a feedback attachment to GCS and return the public URL.

    Files are stored under feedback/{uuid}_{filename} and auto-deleted
    after 15 days by the bucket lifecycle policy.
    """
    try:
        bucket_name = os.environ.get("GCS_BUCKET", "certimate-titi-data")
        from google.cloud import storage as gcs
        client = gcs.Client()
        bucket = client.bucket(bucket_name)

        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        blob_path = f"feedback/{unique_name}"
        blob = bucket.blob(blob_path)

        blob.upload_from_string(file_bytes, content_type=content_type)
        blob.make_public()

        logger.info("Uploaded feedback attachment: %s (%d bytes)", blob_path, len(file_bytes))
        return blob.public_url
    except Exception:
        logger.exception("Failed to upload feedback attachment: %s", filename)
        return None
