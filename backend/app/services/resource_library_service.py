"""資源庫管理 Service。"""

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.resource import Resource, ResourceStatus
from app.models.resource_scaffold import ResourceScaffold
from app.models.resource_parse_job import ResourceParseJob


class ResourceLibraryService:
    """Resource Library Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    def list_resources(self, user_id: str, keyword: str | None = None, subject_id: str | None = None):
        """列出使用者的資源。

        Args:
            user_id: 使用者 ID。
            keyword: 名稱關鍵字過濾（可選）。
            subject_id: 科目 ID 過濾（可選）— 對應 Spec 11 §「提供學科切換器
                過濾不同學科的資源列表」。
        """
        user_uuid = uuid.UUID(user_id)

        query = self.db.query(Resource).filter_by(user_id=user_uuid)

        if keyword:
            query = query.filter(Resource.name.ilike(f"%{keyword}%"))

        if subject_id:
            try:
                sid_uuid = uuid.UUID(subject_id)
                query = query.filter(Resource.subject_id == sid_uuid)
            except ValueError:
                # 無效的 subject_id 視為「無此科目資源」回空列
                return {"resources": []}

        resources = query.order_by(Resource.created_at.desc()).all()

        # 一次性取得所有 resource 的 scaffold count（避免 N+1）
        resource_ids = [r.id for r in resources]
        scaffold_counts: dict = {}
        last_job_status: dict = {}
        last_job_reason: dict = {}
        if resource_ids:
            rows = (
                self.db.query(ResourceScaffold.resource_id, func.count(ResourceScaffold.id))
                .filter(ResourceScaffold.resource_id.in_(resource_ids))
                .group_by(ResourceScaffold.resource_id)
                .all()
            )
            scaffold_counts = {rid: cnt for rid, cnt in rows}

            # 每個 resource 取最新一筆 parse_job 狀態 + failure_reason
            jobs = (
                self.db.query(
                    ResourceParseJob.resource_id,
                    ResourceParseJob.status,
                    ResourceParseJob.failure_reason,
                )
                .filter(ResourceParseJob.resource_id.in_(resource_ids))
                .order_by(ResourceParseJob.resource_id, ResourceParseJob.created_at.desc())
                .all()
            )
            for rid, status, reason in jobs:
                if rid not in last_job_status:  # 取最新一筆
                    last_job_status[rid] = status
                    last_job_reason[rid] = reason

        items = []
        for r in resources:
            scope_val = r.scope.value if hasattr(r.scope, 'value') else str(r.scope)
            # PRD-033 §8：badge 類型對應 scope
            badge = {
                "platform": "official_default",
                "shared": "edu_shared",
                "institution": "institution",
                "personal": "personal",
            }.get(scope_val, "personal")
            # Spec 11 §「資源列表應反映鷹架生成子任務的真實狀態」
            type_val = r.type.value if hasattr(r.type, 'value') else str(r.type)
            scaffold_count = scaffold_counts.get(r.id, 0)
            job_status = last_job_status.get(r.id)

            # 系統生成虛擬資源（考古題題庫）/ 影音類不適用鷹架
            is_virtual = type_val in ('historical_exam',) or (r.name or '').endswith('題庫')
            is_video = type_val in ('youtube_url', 'video')

            if is_virtual or is_video:
                scaffold_status = 'none'
            elif scaffold_count > 0:
                scaffold_status = 'ready'
            elif job_status == 'failed':
                scaffold_status = 'failed'
            elif job_status in ('pending', 'queued', 'processing'):
                scaffold_status = 'pending'
            else:
                # 沒 job 紀錄、沒 scaffold — 視為失敗（chunking 完但 parse 沒跑或無紀錄）
                scaffold_status = 'failed' if r.status.value == 'completed' else 'pending'

            # Spec 11 §「系統應偵測檔案遺失並引導用戶重新上傳」
            reason = (last_job_reason.get(r.id) or '')
            needs_reupload = (
                scaffold_status == 'failed'
                and ('檔案不存在' in reason or 'FileNotFoundError' in reason or 'file not found' in reason.lower())
            )

            items.append({
                "resource_id": str(r.id),
                "name": r.name,
                "type": type_val,
                "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
                "scope": scope_val,
                "badge": badge,
                "subject_id": str(r.subject_id) if r.subject_id else None,
                "scaffold_status": scaffold_status,
                "needs_reupload": needs_reupload,
            })

        return {"resources": items}

    def delete_resource(self, user_id: str, resource_id: str):
        """刪除資源。"""
        user_uuid = uuid.UUID(user_id)
        res_uuid = uuid.UUID(resource_id)

        resource = self.db.query(Resource).filter_by(id=res_uuid).first()
        if not resource:
            return {"error": True, "status_code": 404, "message": "資源不存在"}

        if resource.user_id != user_uuid:
            return {"error": True, "status_code": 403, "message": "無存取此資源的權限"}

        self.db.delete(resource)
        self.db.commit()
        return {"message": "資源已刪除"}

    def heal_orphan_resources(self) -> dict:
        """掃描所有資源，對 gcs_path 對應檔案不存在者新增一筆 failed parse_job。

        Spec 11 §「Admin healing endpoint 自動掃描並標記孤兒資源」
        - 由 admin / 排程觸發
        - 不刪除資源（避免誤刪），只標記 scaffold_status 失敗
        - 重複掃描安全（已標記 failed 的不重複新增）
        """
        from datetime import datetime, timezone
        from app.services.storage_service import get_storage_service
        from app.models.resource_parse_job import ResourceParseJob

        storage = get_storage_service()
        resources = self.db.query(Resource).all()
        marked = 0
        skipped = 0
        for r in resources:
            if not r.gcs_path:
                continue
            try:
                if storage.exists(r.gcs_path):
                    continue
            except Exception:
                continue

            # 檔案不存在；檢查是否已有最新 failed 紀錄
            last_job = (
                self.db.query(ResourceParseJob)
                .filter(ResourceParseJob.resource_id == r.id)
                .order_by(ResourceParseJob.created_at.desc())
                .first()
            )
            reason_text = '檔案不存在'
            if last_job and last_job.status == 'failed' and reason_text in (last_job.failure_reason or ''):
                skipped += 1
                continue

            new_job = ResourceParseJob(
                resource_id=r.id,
                tenant_id=r.tenant_id,
                status='failed',
                failure_reason=f'{reason_text}: {r.gcs_path}（healing job 偵測）',
                finished_at=datetime.now(timezone.utc),
            )
            self.db.add(new_job)
            marked += 1
        self.db.commit()
        return {"marked": marked, "skipped": skipped, "total_scanned": len(resources)}

    def reparse_resource(self, user_id: str, resource_id: str):
        """重新解析資源。"""
        user_uuid = uuid.UUID(user_id)
        res_uuid = uuid.UUID(resource_id)

        resource = self.db.query(Resource).filter_by(id=res_uuid).first()
        if not resource:
            return {"error": True, "status_code": 404, "message": "資源不存在"}

        if resource.user_id != user_uuid:
            return {"error": True, "status_code": 403, "message": "無存取此資源的權限"}

        if resource.status in (ResourceStatus.PENDING, ResourceStatus.PROCESSING):
            return {"error": True, "status_code": 409, "message": "資源正在處理中，請稍後再試"}

        resource.status = ResourceStatus.PENDING
        self.db.commit()
        return {"message": "已重新觸發解析"}
