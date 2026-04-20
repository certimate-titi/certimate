"""PRD-034 — Platform Subject Admin Service.

管理員工作流：草稿 → 發布 → rollback（版本控制）。

Admin 修改 platform subject（scope=platform）的預載資源/節點屬於「草稿」，
直到呼叫 publish 才：
  - version += 1
  - published_at = now()

Rollback：僅能回復 published_at（時間戳記憶體），DB 裡的內容本身沒有歷史快照
（為了簡化，PRD-034 決議：rollback 只重設 published_at=該版本時間，並記錄事件）。

**注意**：rollback 不會復原實際資料內容，只標示「此版本已撤回」；
完整內容回溯需搭配外部備份機制（未納入本次 scope）。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.subject import Subject

logger = logging.getLogger(__name__)


class PlatformSubjectAdminService:
    def __init__(self, db: Session):
        self.db = db

    def update_draft(
        self, platform_subject_id: str, resource_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """編輯 platform subject 的草稿（目前：替換 subject_default_resources 清單）。

        不會 bump version；影響僅限於「之後 fork 的新用戶」— 已 fork 的用戶完全解耦。
        """
        from app.models.subject_default_resource import SubjectDefaultResource

        platform = self._load_platform(platform_subject_id)
        if isinstance(platform, dict):
            return platform

        if resource_ids is not None:
            self.db.query(SubjectDefaultResource).filter(
                SubjectDefaultResource.subject_id == platform.id
            ).delete()
            for rid in resource_ids:
                try:
                    rid_uuid = uuid.UUID(rid)
                except ValueError:
                    return _err(400, f"resource_id 格式錯誤: {rid}")
                self.db.add(
                    SubjectDefaultResource(
                        subject_id=platform.id, resource_id=rid_uuid
                    )
                )
            self.db.commit()
            logger.info(
                "Updated draft of platform subject %s: %d resources",
                platform.id,
                len(resource_ids),
            )

        return {
            "subject_id": str(platform.id),
            "draft_resources": resource_ids if resource_ids is not None else [],
            "version": platform.version,
            "published_at": (
                platform.published_at.isoformat() if platform.published_at else None
            ),
        }

    def publish(self, platform_subject_id: str) -> dict[str, Any]:
        """發布當前草稿：version +1、published_at = now()。"""
        platform = self._load_platform(platform_subject_id)
        if isinstance(platform, dict):
            return platform

        platform.version = (platform.version or 1) + 1
        platform.published_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info(
            "Published platform subject %s -> version=%d",
            platform.id,
            platform.version,
        )
        return {
            "subject_id": str(platform.id),
            "version": platform.version,
            "published_at": platform.published_at.isoformat(),
        }

    def rollback(self, platform_subject_id: str) -> dict[str, Any]:
        """Rollback：版本號退回前一版（published_at 設為 NULL 代表未發布狀態）。

        注意：實際資料內容不會還原，僅版本標記退回。
        """
        platform = self._load_platform(platform_subject_id)
        if isinstance(platform, dict):
            return platform

        if (platform.version or 1) <= 1:
            return _err(400, "已是初始版本，無法 rollback")

        platform.version -= 1
        platform.published_at = None
        self.db.commit()
        logger.warning(
            "Rollback platform subject %s -> version=%d (內容未還原)",
            platform.id,
            platform.version,
        )
        return {
            "subject_id": str(platform.id),
            "version": platform.version,
            "published_at": None,
            "warning": "Rollback 僅退回版本號，實際資料內容未還原",
        }

    def list_versions(self, platform_subject_id: str) -> dict[str, Any]:
        """列出當前版本資訊（PRD-034 簡化版：只有當前 version + published_at）。"""
        platform = self._load_platform(platform_subject_id)
        if isinstance(platform, dict):
            return platform

        return {
            "subject_id": str(platform.id),
            "current_version": platform.version,
            "published_at": (
                platform.published_at.isoformat() if platform.published_at else None
            ),
        }

    def _load_platform(self, platform_subject_id: str):
        try:
            pid = uuid.UUID(platform_subject_id)
        except ValueError:
            return _err(400, "subject_id 格式錯誤")

        platform = self.db.query(Subject).filter(Subject.id == pid).first()
        if not platform:
            return _err(404, "找不到平台科目")
        if platform.scope != "platform":
            return _err(400, "只能操作 scope=platform 的科目")
        return platform


def _err(status_code: int, message: str) -> dict[str, Any]:
    return {"error": True, "status_code": status_code, "message": message}
