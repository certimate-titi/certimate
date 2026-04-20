"""PRD-034 — Platform Subject Fork Service.

用戶選擇平台 platform subject（有預載資源）時，一次性複製：
1. subject_default_resources 裡的 resources（改 owner 為 user）
2. GCS 檔案（新的 user_id/resource_id 路徑）
3. platform 的 knowledge_nodes（FK 重指向新 resource_ids）

複製完成後，subject 對此用戶完全解耦 — platform 後續變更不影響該用戶。

冪等性：若該用戶已 fork 過同一個 platform subject（透過 source_platform_subject_id 判斷），
回傳 409。

原子性：整個複製在單一 DB transaction 內；任何一步失敗就 rollback 並清理已複製的 GCS 檔。
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceScope
from app.models.subject import Subject
from app.models.subject_default_resource import SubjectDefaultResource
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)


class SubjectForkService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage_service()

    def fork_platform_subject(
        self, user_id: str, platform_subject_id: str
    ) -> dict[str, Any]:
        """將 platform subject 的預載資源與知識節點複製到 user 的 personal subject。

        回傳：
          - 成功：{"subject_id": str, "resources_copied": int, "nodes_copied": int}
          - 失敗：{"error": True, "status_code": int, "message": str}
        """
        user_uuid = uuid.UUID(user_id)
        platform_uuid = uuid.UUID(platform_subject_id)

        platform = self.db.query(Subject).filter(Subject.id == platform_uuid).first()
        if not platform:
            return _err(404, "找不到平台科目")
        if platform.scope != "platform":
            return _err(400, "只能 fork scope=platform 的科目")

        existing = (
            self.db.query(Subject)
            .filter(
                Subject.owner_user_id == user_uuid,
                Subject.source_platform_subject_id == platform_uuid,
            )
            .first()
        )
        if existing:
            return _err(
                409,
                f"您已擁有此科目（subject_id={existing.id}）",
            )

        copied_gcs_paths: list[str] = []
        try:
            user_subject = Subject(
                id=uuid.uuid4(),
                category_id=platform.category_id,
                name=platform.name,
                name_en=platform.name_en,
                description=platform.description,
                parent_subject_id=platform.parent_subject_id,
                is_popular=False,
                exam_subject_codes=platform.exam_subject_codes,
                owner_user_id=user_uuid,
                scope="personal",
                source_platform_subject_id=platform_uuid,
                version=1,
            )
            self.db.add(user_subject)
            self.db.flush()

            default_links = (
                self.db.query(SubjectDefaultResource)
                .filter(SubjectDefaultResource.subject_id == platform_uuid)
                .all()
            )
            platform_resource_ids = [link.resource_id for link in default_links]

            resource_id_map: dict[uuid.UUID, uuid.UUID] = {}
            for platform_rid in platform_resource_ids:
                platform_res = (
                    self.db.query(Resource).filter(Resource.id == platform_rid).first()
                )
                if not platform_res:
                    continue

                new_rid = uuid.uuid4()
                new_gcs_path: str | None = None
                if platform_res.gcs_path:
                    new_gcs_path = self.storage.copy_file(
                        src_path=platform_res.gcs_path,
                        dst_user_id=str(user_uuid),
                        dst_resource_id=str(new_rid),
                        dst_filename=platform_res.name,
                    )
                    copied_gcs_paths.append(new_gcs_path)

                user_res = Resource(
                    id=new_rid,
                    user_id=user_uuid,
                    subject_id=user_subject.id,
                    name=platform_res.name,
                    type=platform_res.type,
                    scope=ResourceScope.PERSONAL,
                    status=platform_res.status,
                    file_size_bytes=platform_res.file_size_bytes,
                    gcs_path=new_gcs_path,
                    youtube_url=platform_res.youtube_url,
                    processing_engine=platform_res.processing_engine,
                    implicit_consent=platform_res.implicit_consent,
                    tags=platform_res.tags,
                )
                self.db.add(user_res)
                resource_id_map[platform_rid] = new_rid

            platform_nodes = (
                self.db.query(KnowledgeNode)
                .filter(KnowledgeNode.subject_id == platform_uuid)
                .all()
            )
            node_id_map: dict[uuid.UUID, uuid.UUID] = {
                n.id: uuid.uuid4() for n in platform_nodes
            }

            nodes_copied = 0
            for pn in platform_nodes:
                new_resource_id = (
                    resource_id_map.get(pn.resource_id) if pn.resource_id else None
                )
                new_parent_id = node_id_map.get(pn.parent_id) if pn.parent_id else None

                user_node = KnowledgeNode(
                    id=node_id_map[pn.id],
                    resource_id=new_resource_id,
                    subject_id=user_subject.id,
                    parent_id=new_parent_id,
                    name=pn.name,
                    depth=pn.depth,
                    sort_order=pn.sort_order,
                    source_page_number=pn.source_page_number,
                    source_timestamp_seconds=pn.source_timestamp_seconds,
                    source_text=pn.source_text,
                    available_questions=pn.available_questions,
                    exam_frequency=pn.exam_frequency,
                    source_origin=pn.source_origin,
                    support_strength=pn.support_strength,
                    syllabus_topic_id=pn.syllabus_topic_id,
                    node_source=pn.node_source,
                    source_resource_count=1,
                )
                self.db.add(user_node)
                nodes_copied += 1

            self.db.commit()
            logger.info(
                "Forked platform subject %s -> user subject %s "
                "(resources=%d, nodes=%d)",
                platform_uuid,
                user_subject.id,
                len(resource_id_map),
                nodes_copied,
            )
            return {
                "user_subject_id": str(user_subject.id),
                "subject_id": str(user_subject.id),
                "resources_copied": len(resource_id_map),
                "nodes_copied": nodes_copied,
            }

        except Exception as exc:
            self.db.rollback()
            logger.exception("Fork failed, cleaning up %d GCS files", len(copied_gcs_paths))
            for path in copied_gcs_paths:
                try:
                    self.storage.delete_file(path)
                except Exception:
                    logger.exception("Cleanup failed for %s", path)
            return _err(500, f"Fork 失敗：{exc}")


def _err(status_code: int, message: str) -> dict[str, Any]:
    return {"error": True, "status_code": status_code, "message": message}
