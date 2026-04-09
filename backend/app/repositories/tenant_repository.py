"""TenantRepository — SQLAlchemy CRUD for tenants table."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.core.config import PUBLIC_B2C_TENANT_ID  # noqa: F401


class TenantRepository:
    """多租戶 Repository — 提供 CRUD 與查詢操作。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """依 UUID 查詢租戶。"""
        import uuid
        try:
            uid = uuid.UUID(str(tenant_id))
        except ValueError:
            return None
        return self.session.query(Tenant).filter(Tenant.id == uid).first()

    def find_by_slug(self, slug: str) -> Optional[Tenant]:
        """依 slug 查詢租戶（slug 為唯一識別碼）。"""
        return self.session.query(Tenant).filter(Tenant.slug == slug).first()

    def find_all_active(self) -> list[Tenant]:
        """查詢所有啟用中的租戶。"""
        return self.session.query(Tenant).filter(Tenant.is_active.is_(True)).all()

    def save(self, tenant: Tenant) -> Tenant:
        """新增或更新租戶。"""
        self.session.merge(tenant)
        self.session.commit()
        return tenant

    def mark_inactive(self, tenant_id: str) -> Optional[Tenant]:
        """將租戶標記為停用（is_active = False）。"""
        tenant = self.find_by_id(tenant_id)
        if tenant:
            tenant.is_active = False
            self.session.commit()
        return tenant

    def count_resources(self, tenant_id: str) -> int:
        """統計租戶擁有的資源數量。"""
        from app.models.resource import Resource
        import uuid
        uid = uuid.UUID(str(tenant_id))
        return self.session.query(Resource).filter(Resource.tenant_id == uid).count()

    def count_resource_chunks(self, tenant_id: str) -> int:
        """統計租戶擁有的 resource_chunks 數量。"""
        from app.models.resource_chunk import ResourceChunk
        import uuid
        uid = uuid.UUID(str(tenant_id))
        return self.session.query(ResourceChunk).filter(ResourceChunk.tenant_id == uid).count()

    def count_answers(self, tenant_id: str) -> int:
        """統計租戶擁有的 answers 數量（含個資，RLS 保護）。"""
        from app.models.answer import Answer
        import uuid
        uid = uuid.UUID(str(tenant_id))
        return self.session.query(Answer).filter(Answer.tenant_id == uid).count()

    def count_exams(self, tenant_id: str) -> int:
        """統計租戶擁有的 exams 數量。"""
        from app.models.exam import Exam
        import uuid
        uid = uuid.UUID(str(tenant_id))
        return self.session.query(Exam).filter(Exam.tenant_id == uid).count()

    def purge_tenant_data(self, tenant_id: str, dry_run: bool = True) -> dict:
        """
        清除租戶所有資料（退場抹除）。
        dry_run=True 時只統計不刪除；dry_run=False 時實際刪除（需管理員確認）。

        禁止刪除 public_b2c 預設租戶。
        """
        if str(tenant_id) == PUBLIC_B2C_TENANT_ID:
            raise ValueError("禁止刪除 public_b2c 預設租戶")

        stats = {
            "tenant_id": str(tenant_id),
            "dry_run": dry_run,
            "resources": self.count_resources(tenant_id),
            "resource_chunks": self.count_resource_chunks(tenant_id),
            "answers": self.count_answers(tenant_id),
            "exams": self.count_exams(tenant_id),
        }

        if not dry_run:
            import uuid
            uid = uuid.UUID(str(tenant_id))
            from app.models.resource import Resource
            from app.models.resource_chunk import ResourceChunk
            from app.models.answer import Answer
            from app.models.exam import Exam

            # 按依賴順序刪除
            self.session.query(Answer).filter(Answer.tenant_id == uid).delete()
            self.session.query(ResourceChunk).filter(ResourceChunk.tenant_id == uid).delete()
            self.session.query(Resource).filter(Resource.tenant_id == uid).delete()
            self.session.query(Exam).filter(Exam.tenant_id == uid).delete()

            # 最後刪除租戶本身
            self.session.query(Tenant).filter(Tenant.id == uid).delete()
            self.session.commit()

            stats["deleted"] = True

        return stats
