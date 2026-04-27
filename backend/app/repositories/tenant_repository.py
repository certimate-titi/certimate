"""TenantRepository — SQLAlchemy CRUD for tenants table."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.core.config import PUBLIC_B2C_TENANT_ID  # noqa: F401


class TenantRepository:
    """多租戶資料存取 Repository。

    封裝 Tenant ORM 的 CRUD、租戶資料量統計與整租戶資料抹除，供 B2B
    機構管理 service 使用。
    """

    def __init__(self, session: Session) -> None:
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def find_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """依 UUID 查詢租戶。

        Args:
            tenant_id: 租戶 UUID 字串；非合法 UUID 字串會回傳 None。

        Returns:
            Tenant 物件；若不存在或字串非法回傳 None。
        """
        import uuid
        try:
            uid = uuid.UUID(str(tenant_id))
        except ValueError:
            return None
        return self.session.query(Tenant).filter(Tenant.id == uid).first()

    def find_by_slug(self, slug: str) -> Optional[Tenant]:
        """依 slug 查詢租戶。

        Args:
            slug: 租戶 slug（唯一識別字串）。

        Returns:
            Tenant 物件；若不存在回傳 None。
        """
        return self.session.query(Tenant).filter(Tenant.slug == slug).first()

    def find_all_active(self) -> list[Tenant]:
        """查詢所有啟用中（``is_active=True``）的租戶。

        Returns:
            list of Tenant。
        """
        return self.session.query(Tenant).filter(Tenant.is_active.is_(True)).all()

    def save(self, tenant: Tenant) -> Tenant:
        """以 merge 方式新增或更新租戶並 commit。

        Args:
            tenant: 待儲存的 Tenant 實例。

        Returns:
            合併後的 Tenant 實例。
        """
        self.session.merge(tenant)
        self.session.commit()
        return tenant

    def mark_inactive(self, tenant_id: str) -> Optional[Tenant]:
        """將租戶標記為停用（``is_active=False``）。

        Args:
            tenant_id: 租戶 UUID 字串。

        Returns:
            更新後的 Tenant；若租戶不存在則回傳 None。
        """
        tenant = self.find_by_id(tenant_id)
        if tenant:
            tenant.is_active = False
            self.session.commit()
        return tenant

    def count_resources(self, tenant_id: str) -> int:
        """統計租戶擁有的 resources 數量。

        Args:
            tenant_id: 租戶 UUID 字串。

        Returns:
            該租戶 resources row 數。
        """
        from app.models.resource import Resource
        import uuid
        uid = uuid.UUID(str(tenant_id))
        return self.session.query(Resource).filter(Resource.tenant_id == uid).count()

    def count_resource_chunks(self, tenant_id: str) -> int:
        """統計租戶擁有的 resource_chunks 數量。

        Args:
            tenant_id: 租戶 UUID 字串。

        Returns:
            該租戶 resource_chunks row 數。
        """
        from app.models.resource_chunk import ResourceChunk
        import uuid
        uid = uuid.UUID(str(tenant_id))
        return self.session.query(ResourceChunk).filter(ResourceChunk.tenant_id == uid).count()

    def count_answers(self, tenant_id: str) -> int:
        """統計租戶擁有的 answers 數量（含個資，RLS 保護）。

        Args:
            tenant_id: 租戶 UUID 字串。

        Returns:
            該租戶 answers row 數。
        """
        from app.models.answer import Answer
        import uuid
        uid = uuid.UUID(str(tenant_id))
        return self.session.query(Answer).filter(Answer.tenant_id == uid).count()

    def count_exams(self, tenant_id: str) -> int:
        """統計租戶擁有的 exams 數量。

        Args:
            tenant_id: 租戶 UUID 字串。

        Returns:
            該租戶 exams row 數。
        """
        from app.models.exam import Exam
        import uuid
        uid = uuid.UUID(str(tenant_id))
        return self.session.query(Exam).filter(Exam.tenant_id == uid).count()

    def purge_tenant_data(self, tenant_id: str, dry_run: bool = True) -> dict:
        """清除租戶所有資料（退場抹除）。

        Args:
            tenant_id: 租戶 UUID 字串。
            dry_run: True（預設）僅統計不刪除；False 時實際依依賴順序刪除
                answers → resource_chunks → resources → exams → tenant 本身，
                需管理員確認。

        Returns:
            dict 含 ``tenant_id``、``dry_run`` 及各表 row 數；若 ``dry_run=False``
            另含 ``deleted=True``。

        Raises:
            ValueError: 嘗試刪除 public_b2c 預設租戶。
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
