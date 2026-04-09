"""BaseService — 統一的 Service 層基底類別.

所有新建 Service 都應繼承此類別。提供：
- 統一的 DB session 管理
- 標準化的查詢/建立/更新 helper
- 錯誤回傳格式統一

現有 Service（33 個）直接使用 self.db.query() 是歷史遺留��
新功能開發 **必須** 使用 BaseService 或對應的 Repository。

使用範例：
    class NewFeatureService(BaseService):
        def do_something(self, user_id: str) -> dict:
            user = self.get_or_404(User, user_id)
            ...
            return self.ok({"result": "done"})
"""

from typing import TypeVar, Type, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Base

T = TypeVar("T", bound=Base)


class BaseService:
    """Service 基底類別，提供統一的 DB 存取模式。"""

    def __init__(self, db: Session):
        self.db = db

    # ── 查詢 helpers ───────────────────────────────────────────────

    def get_or_404(self, model: Type[T], entity_id: str | UUID) -> T:
        """根據 ID 查詢實體，不存在則回傳 404 錯誤。"""
        if isinstance(entity_id, str):
            try:
                entity_id = UUID(entity_id)
            except ValueError:
                return self.error(f"無效的 ID 格式: {entity_id}", 400)

        entity = self.db.query(model).filter(model.id == entity_id).first()
        if not entity:
            return self.error(f"{model.__tablename__} 不存在: {entity_id}", 404)
        return entity

    def get_by_id(self, model: Type[T], entity_id: str | UUID) -> Optional[T]:
        """根據 ID 查詢實體，不存在回傳 None。"""
        if isinstance(entity_id, str):
            try:
                entity_id = UUID(entity_id)
            except ValueError:
                return None
        return self.db.query(model).filter(model.id == entity_id).first()

    # ── 回��格式 helpers ──────────────────────────────────────────

    @staticmethod
    def ok(data: dict = None, message: str = "操作成功") -> dict:
        """成功回傳。"""
        result = {"ok": True, "message": message}
        if data:
            result.update(data)
        return result

    @staticmethod
    def error(message: str, status_code: int = 400) -> dict:
        """錯誤回傳（統一格式）。"""
        return {"error": True, "status_code": status_code, "message": message}

    # ��─ 交易 helpers ──────────────────────────────────────────────

    def commit(self):
        """提交交易。"""
        self.db.commit()

    def flush(self):
        """Flush 但不提交。"""
        self.db.flush()

    def rollback(self):
        """回滾交易。"""
        self.db.rollback()
