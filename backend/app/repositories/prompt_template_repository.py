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
    """Prompt 模板資料存取層。"""

    def __init__(self, session: Session):
        self.session = session

    # ── Template CRUD ─────────────────────────────────────────────────────

    def save(self, template: PromptTemplateV2) -> PromptTemplateV2:
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template

    def find_all(self, category: Optional[str] = None) -> list[PromptTemplateV2]:
        q = self.session.query(PromptTemplateV2)
        if category:
            q = q.filter(PromptTemplateV2.category == category)
        return q.order_by(PromptTemplateV2.template_id).all()

    def find_by_template_id(self, template_id: str) -> Optional[PromptTemplateV2]:
        return (
            self.session.query(PromptTemplateV2)
            .filter_by(template_id=template_id)
            .first()
        )

    def find_by_name(self, name: str) -> Optional[PromptTemplateV2]:
        return (
            self.session.query(PromptTemplateV2)
            .filter_by(name=name)
            .first()
        )

    def exists_by_template_id(self, template_id: str) -> bool:
        return (
            self.session.query(PromptTemplateV2)
            .filter_by(template_id=template_id)
            .count()
            > 0
        )

    def exists_by_name(self, name: str) -> bool:
        return (
            self.session.query(PromptTemplateV2)
            .filter_by(name=name)
            .count()
            > 0
        )

    # ── Version ───────────────────────────────────────────────────────────

    def save_version(self, version: PromptTemplateVersion) -> PromptTemplateVersion:
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        return version

    def find_versions(self, template_uuid: uuid.UUID) -> list[PromptTemplateVersion]:
        return (
            self.session.query(PromptTemplateVersion)
            .filter_by(template_id=template_uuid)
            .order_by(PromptTemplateVersion.version.desc())
            .all()
        )

    def find_version(
        self, template_uuid: uuid.UUID, version: int
    ) -> Optional[PromptTemplateVersion]:
        return (
            self.session.query(PromptTemplateVersion)
            .filter_by(template_id=template_uuid, version=version)
            .first()
        )

    def count_versions(self, template_uuid: uuid.UUID) -> int:
        return (
            self.session.query(PromptTemplateVersion)
            .filter_by(template_id=template_uuid)
            .count()
        )

    # ── A/B Test ──────────────────────────────────────────────────────────

    def save_ab_test(self, ab_test: PromptAbTest) -> PromptAbTest:
        self.session.add(ab_test)
        self.session.commit()
        self.session.refresh(ab_test)
        return ab_test

    def find_running_ab_test(
        self, template_uuid: uuid.UUID
    ) -> Optional[PromptAbTest]:
        return (
            self.session.query(PromptAbTest)
            .filter_by(template_id=template_uuid, status=AbTestStatus.RUNNING)
            .first()
        )

    def find_ab_test_by_id(self, test_id: str) -> Optional[PromptAbTest]:
        try:
            uid = uuid.UUID(test_id)
        except ValueError:
            return None
        return self.session.query(PromptAbTest).filter_by(id=uid).first()

    def find_ab_test_by_name(self, name: str) -> Optional[PromptAbTest]:
        return (
            self.session.query(PromptAbTest)
            .filter_by(name=name)
            .first()
        )

    def find_all_ab_tests(self) -> list[PromptAbTest]:
        return (
            self.session.query(PromptAbTest)
            .order_by(PromptAbTest.created_at.desc())
            .all()
        )
