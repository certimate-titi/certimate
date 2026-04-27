"""Prompt Template Repository — SQLAlchemy 實作 (Feature 30)."""

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.prompt_template import (
    PromptTemplateV2,
    PromptTemplateVersion,
    PromptAbTest,
    AbTestStatus,
)


class PromptTemplateRepository:
    """Prompt 模板資料存取 Repository（Feature 30）。

    封裝 PromptTemplateV2、PromptTemplateVersion、PromptAbTest 三個
    ORM 的查詢與儲存，供 Prompt 管理 service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    # ── Template CRUD ─────────────────────────────────────────────────────

    def save(self, template: PromptTemplateV2) -> PromptTemplateV2:
        """新增或更新 Prompt 模板並 commit。

        Args:
            template: 待儲存的 PromptTemplateV2 實例。

        Returns:
            已 refresh 的 PromptTemplateV2 實例。
        """
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template

    def find_all(self, category: Optional[str] = None) -> list[PromptTemplateV2]:
        """列出所有 Prompt 模板，依 template_id 升冪排序。

        Args:
            category: 可選的分類過濾；若為 None 則列出所有分類。

        Returns:
            list of PromptTemplateV2。
        """
        q = self.session.query(PromptTemplateV2)
        if category:
            q = q.filter(PromptTemplateV2.category == category)
        return q.order_by(PromptTemplateV2.template_id).all()

    def find_by_template_id(self, template_id: str) -> Optional[PromptTemplateV2]:
        """依 template_id 字串查詢模板。

        Args:
            template_id: 模板識別字串（人為命名，例如 ``ai_chat_default``）。

        Returns:
            PromptTemplateV2 物件；若不存在回傳 None。
        """
        return (
            self.session.query(PromptTemplateV2)
            .filter_by(template_id=template_id)
            .first()
        )

    def find_by_name(self, name: str) -> Optional[PromptTemplateV2]:
        """依顯示名稱查詢模板。

        Args:
            name: 模板顯示名稱。

        Returns:
            PromptTemplateV2 物件；若不存在回傳 None。
        """
        return (
            self.session.query(PromptTemplateV2)
            .filter_by(name=name)
            .first()
        )

    def exists_by_template_id(self, template_id: str) -> bool:
        """檢查 template_id 是否已存在。

        Args:
            template_id: 模板識別字串。

        Returns:
            True 表示已存在。
        """
        return (
            self.session.query(PromptTemplateV2)
            .filter_by(template_id=template_id)
            .count()
            > 0
        )

    def exists_by_name(self, name: str) -> bool:
        """檢查模板顯示名稱是否已存在。

        Args:
            name: 模板顯示名稱。

        Returns:
            True 表示已存在。
        """
        return (
            self.session.query(PromptTemplateV2)
            .filter_by(name=name)
            .count()
            > 0
        )

    # ── Version ───────────────────────────────────────────────────────────

    def save_version(self, version: PromptTemplateVersion) -> PromptTemplateVersion:
        """新增或更新模板版本並 commit。

        Args:
            version: 待儲存的 PromptTemplateVersion 實例。

        Returns:
            已 refresh 的 PromptTemplateVersion 實例。
        """
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        return version

    def find_versions(self, template_uuid: uuid.UUID) -> list[PromptTemplateVersion]:
        """查詢模板的所有版本，依版本號降冪排序。

        Args:
            template_uuid: PromptTemplateV2 主鍵 UUID。

        Returns:
            list of PromptTemplateVersion。
        """
        return (
            self.session.query(PromptTemplateVersion)
            .filter_by(template_id=template_uuid)
            .order_by(PromptTemplateVersion.version.desc())
            .all()
        )

    def find_version(
        self, template_uuid: uuid.UUID, version: int
    ) -> Optional[PromptTemplateVersion]:
        """依模板與版本號查詢特定版本。

        Args:
            template_uuid: PromptTemplateV2 主鍵 UUID。
            version: 版本號。

        Returns:
            PromptTemplateVersion 物件；若不存在回傳 None。
        """
        return (
            self.session.query(PromptTemplateVersion)
            .filter_by(template_id=template_uuid, version=version)
            .first()
        )

    def count_versions(self, template_uuid: uuid.UUID) -> int:
        """統計模板的版本數量。

        Args:
            template_uuid: PromptTemplateV2 主鍵 UUID。

        Returns:
            該模板的版本總數。
        """
        return (
            self.session.query(PromptTemplateVersion)
            .filter_by(template_id=template_uuid)
            .count()
        )

    # ── A/B Test ──────────────────────────────────────────────────────────

    def save_ab_test(self, ab_test: PromptAbTest) -> PromptAbTest:
        """新增或更新 A/B 測試並 commit。

        Args:
            ab_test: 待儲存的 PromptAbTest 實例。

        Returns:
            已 refresh 的 PromptAbTest 實例。
        """
        self.session.add(ab_test)
        self.session.commit()
        self.session.refresh(ab_test)
        return ab_test

    def find_running_ab_test(
        self, template_uuid: uuid.UUID
    ) -> Optional[PromptAbTest]:
        """查詢模板目前進行中的 A/B 測試。

        Args:
            template_uuid: PromptTemplateV2 主鍵 UUID。

        Returns:
            ``status=RUNNING`` 的 PromptAbTest；若無則回傳 None。
        """
        return (
            self.session.query(PromptAbTest)
            .filter_by(template_id=template_uuid, status=AbTestStatus.RUNNING)
            .first()
        )

    def find_ab_test_by_id(self, test_id: str) -> Optional[PromptAbTest]:
        """依字串型別 test_id 查詢 A/B 測試。

        Args:
            test_id: PromptAbTest 主鍵的字串表示；不合法的 UUID 字串會回傳 None。

        Returns:
            PromptAbTest 物件；若 test_id 非法或不存在則回傳 None。
        """
        try:
            uid = uuid.UUID(test_id)
        except ValueError:
            return None
        return self.session.query(PromptAbTest).filter_by(id=uid).first()

    def find_ab_test_by_name(self, name: str) -> Optional[PromptAbTest]:
        """依名稱查詢 A/B 測試。

        Args:
            name: A/B 測試名稱。

        Returns:
            PromptAbTest 物件；若不存在回傳 None。
        """
        return (
            self.session.query(PromptAbTest)
            .filter_by(name=name)
            .first()
        )

    def find_all_ab_tests(self) -> list[PromptAbTest]:
        """列出所有 A/B 測試，依 created_at 降冪排序。

        Returns:
            list of PromptAbTest。
        """
        return (
            self.session.query(PromptAbTest)
            .order_by(PromptAbTest.created_at.desc())
            .all()
        )
