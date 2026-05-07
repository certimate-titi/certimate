"""Subject Service — hard delete with cascade count preview.

此 service 提供：
1. get_delete_preview()：計算刪除 subject 時的連帶影響筆數（SUPER_ADMIN 專用）
2. hard_delete_subject()：硬刪 subject，依賴 DB CASCADE FK 自動清子資料
   （exams 無 CASCADE，須手動刪；其餘透過 FK CASCADE 自動處理）
"""

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 輔助：計算 cascade 影響筆數
# ---------------------------------------------------------------------------

def _count_cascade_for_subject(db: Session, subject_id: uuid.UUID) -> dict[str, int]:
    """計算刪除 subject 時將連帶刪除的各表筆數。

    回傳 dict，key 為資料表名稱，value 為筆數。
    此函式只做 SELECT COUNT，不做任何修改。
    """
    from sqlalchemy import text as _text

    sid = str(subject_id)
    counts: dict[str, int] = {}

    # 直接掛 subjects.id 的表
    tables_direct = [
        "resources",
        "knowledge_nodes",
        "learning_journeys",
        "exams",
        "syllabus_topics",
        "subject_default_resources",
        "reverse_engineering_tasks",
        "merge_conflicts",
        "merge_histories",
    ]
    for tbl in tables_direct:
        try:
            row = db.execute(
                _text(f"SELECT COUNT(*) FROM {tbl} WHERE subject_id = :sid"),
                {"sid": sid},
            ).fetchone()
            counts[tbl] = int(row[0]) if row else 0
        except Exception:
            counts[tbl] = -1  # 表不存在或欄位不同名時標 -1

    # exams 下的 questions（透過 exam_id）
    try:
        row = db.execute(
            _text(
                "SELECT COUNT(*) FROM questions q "
                "JOIN exams e ON q.exam_id = e.id "
                "WHERE e.subject_id = :sid"
            ),
            {"sid": sid},
        ).fetchone()
        counts["questions"] = int(row[0]) if row else 0
    except Exception:
        counts["questions"] = -1

    # answers（透過 exam_id）
    try:
        row = db.execute(
            _text(
                "SELECT COUNT(*) FROM answers a "
                "JOIN exams e ON a.exam_id = e.id "
                "WHERE e.subject_id = :sid"
            ),
            {"sid": sid},
        ).fetchone()
        counts["answers"] = int(row[0]) if row else 0
    except Exception:
        counts["answers"] = -1

    # resource 相關子表（透過 resource_id）
    resource_child_tables = [
        "resource_chunks",
        "resource_parse_jobs",
        "resource_scaffolds",
        "question_candidates",
    ]
    for tbl in resource_child_tables:
        try:
            row = db.execute(
                _text(
                    f"SELECT COUNT(*) FROM {tbl} c "
                    f"JOIN resources r ON c.resource_id = r.id "
                    f"WHERE r.subject_id = :sid"
                ),
                {"sid": sid},
            ).fetchone()
            counts[tbl] = int(row[0]) if row else 0
        except Exception:
            counts[tbl] = -1

    return counts


# ---------------------------------------------------------------------------
# 輔助：計算 cascade 影響筆數（resource 版）
# ---------------------------------------------------------------------------

def _count_cascade_for_resource(db: Session, resource_id: uuid.UUID) -> dict[str, int]:
    """計算刪除 resource 時將連帶刪除的各表筆數。"""
    from sqlalchemy import text as _text

    rid = str(resource_id)
    counts: dict[str, int] = {}

    tables = [
        "resource_chunks",
        "resource_parse_jobs",
        "resource_scaffolds",
        "question_candidates",
        "knowledge_nodes",
        "user_hidden_resources",
    ]
    for tbl in tables:
        try:
            row = db.execute(
                _text(f"SELECT COUNT(*) FROM {tbl} WHERE resource_id = :rid"),
                {"rid": rid},
            ).fetchone()
            counts[tbl] = int(row[0]) if row else 0
        except Exception:
            counts[tbl] = -1

    return counts


# ---------------------------------------------------------------------------
# Subject hard-delete service
# ---------------------------------------------------------------------------

class SubjectDeleteService:
    """Subject 硬刪除服務（SUPER_ADMIN 專用）。"""

    def __init__(self, db: Session):
        self.db = db

    def get_delete_preview(
        self, subject_id: str, super_admin: User
    ) -> dict[str, Any]:
        """取得刪除 subject 的連帶影響筆數，不做任何修改。

        Args:
            subject_id: 要刪除的 subject UUID 字串
            super_admin: 已通過 require_super_admin dependency 的 User 物件

        Returns:
            {"subject_id": ..., "subject_name": ..., "cascade_count": {...}}

        Raises:
            HTTPException 404: subject 不存在
        """
        from fastapi import HTTPException

        try:
            sid = uuid.UUID(subject_id)
        except ValueError:
            raise HTTPException(status_code=400, detail={"message": "subject_id 格式無效"})

        subject = self.db.query(Subject).filter(Subject.id == sid).first()
        if subject is None:
            raise HTTPException(status_code=404, detail={"message": "科目不存在"})

        cascade_count = _count_cascade_for_subject(self.db, sid)
        return {
            "subject_id": subject_id,
            "subject_name": subject.name,
            "cascade_count": cascade_count,
        }

    def hard_delete_subject(
        self, subject_id: str, super_admin: User
    ) -> dict[str, Any]:
        """硬刪 subject 及所有連帶資料（SUPER_ADMIN 專用）。

        刪除順序：
        1. 先計算 cascade_count（用於回傳統計）
        2. 手動刪除 exams（因 FK 無 CASCADE）→ 連帶 answers/questions 透過 CASCADE
        3. 刪除 resources（其子表 chunks/scaffolds/parse_jobs 等透過 CASCADE）
        4. 刪除 Subject row（knowledge_nodes/learning_journeys 等透過 CASCADE）

        Args:
            subject_id: 要刪除的 subject UUID 字串
            super_admin: 已通過 require_super_admin dependency 的 User 物件

        Returns:
            {"deleted": True, "subject_id": ..., "cascade_count": {...}}

        Raises:
            HTTPException 404: subject 不存在
            HTTPException 500: 刪除失敗（rollback）
        """
        from fastapi import HTTPException
        from sqlalchemy import text as _text
        from app.models.exam import Exam
        from app.models.resource import Resource

        try:
            sid = uuid.UUID(subject_id)
        except ValueError:
            raise HTTPException(status_code=400, detail={"message": "subject_id 格式無效"})

        subject = self.db.query(Subject).filter(Subject.id == sid).first()
        if subject is None:
            raise HTTPException(status_code=404, detail={"message": "科目不存在"})

        # 事前統計（回傳用）
        cascade_count = _count_cascade_for_subject(self.db, sid)

        try:
            # Step 1: 清 orphan questions（防 ck_questions_has_parent 觸發）
            self.db.execute(
                _text("DELETE FROM questions WHERE exam_id IS NULL AND historical_exam_id IS NULL")
            )

            # Step 2: 手動刪 exams（FK subjects.id 無 CASCADE）
            # answers、questions 透過 exam_id CASCADE 自動清
            exams = self.db.query(Exam).filter(Exam.subject_id == sid).all()
            for exam in exams:
                self.db.delete(exam)
            self.db.flush()

            # Step 3: 刪 resources（子表透過 CASCADE 自動清）
            resources = self.db.query(Resource).filter(Resource.subject_id == sid).all()
            for res in resources:
                self.db.delete(res)
            self.db.flush()

            # Step 4: 刪 Subject（knowledge_nodes, learning_journeys, syllabus_topics 等透過 CASCADE）
            self.db.delete(subject)

            # Step 5: 寫 admin_audit_logs（不可逆操作必留 audit）
            from app.models.audit_log import AdminAuditLog
            from app.core.permissions import AuditAction
            self.db.add(AdminAuditLog(
                admin_id=super_admin.id,
                action=AuditAction.SUBJECT_HARD_DELETED,
                target_type="subject",
                target_id=uuid.UUID(subject_id) if isinstance(subject_id, str) else subject_id,
                details={"cascade_count": cascade_count, "subject_name": getattr(subject, "name", None)},
            ))
            self.db.commit()

        except Exception as exc:
            self.db.rollback()
            logger.exception("hard_delete_subject failed for subject_id=%s: %s", subject_id, exc)
            raise HTTPException(
                status_code=500,
                detail={"message": f"刪除失敗：{type(exc).__name__}: {str(exc)[:300]}"},
            )

        logger.info(
            "hard_delete_subject completed: subject_id=%s by super_admin=%s cascade=%s",
            subject_id,
            super_admin.id,
            cascade_count,
        )
        return {
            "deleted": True,
            "subject_id": subject_id,
            "cascade_count": cascade_count,
        }


# ---------------------------------------------------------------------------
# Resource hard-delete service
# ---------------------------------------------------------------------------

class ResourceDeleteService:
    """Resource 硬刪除服務（擁有者專用）。"""

    def __init__(self, db: Session):
        self.db = db

    def get_delete_preview(
        self, resource_id: str, user_id: str
    ) -> dict[str, Any]:
        """取得刪除 resource 的連帶影響筆數，不做任何修改。

        Args:
            resource_id: 要刪除的 resource UUID 字串
            user_id: 當前使用者 ID（從 JWT 解析）

        Returns:
            {"resource_id": ..., "resource_name": ..., "cascade_count": {...}}

        Raises:
            HTTPException 404: resource 不存在或不屬於本人
        """
        from fastapi import HTTPException
        from app.models.resource import Resource

        try:
            rid = uuid.UUID(resource_id)
        except ValueError:
            raise HTTPException(status_code=400, detail={"message": "resource_id 格式無效"})

        # 不過濾 user_id；非擁有者走 soft-hide preview（cascade 全 0，僅標示會隱藏）
        resource = self.db.query(Resource).filter(Resource.id == rid).first()
        if resource is None:
            raise HTTPException(status_code=404, detail={"message": "資源不存在"})

        is_owner = resource.user_id == uuid.UUID(user_id)
        if not is_owner:
            return {
                "resource_id": resource_id,
                "resource_name": resource.name,
                "cascade_count": {"user_hidden_resources": 1},
                "is_owner": False,
            }

        cascade_count = _count_cascade_for_resource(self.db, rid)
        return {
            "resource_id": resource_id,
            "resource_name": resource.name,
            "cascade_count": cascade_count,
            "is_owner": True,
        }

    def hard_delete_resource(
        self, resource_id: str, user_id: str
    ) -> dict[str, Any]:
        """硬刪 resource 及連帶子資料（擁有者專用）。

        子表（chunks, parse_jobs, scaffolds, question_candidates, knowledge_nodes）
        透過 DB FK CASCADE 自動清除。

        Args:
            resource_id: 要刪除的 resource UUID 字串
            user_id: 當前使用者 ID

        Returns:
            {"deleted": True, "resource_id": ..., "cascade_count": {...}}

        Raises:
            HTTPException 404: resource 不存在或不屬於本人
            HTTPException 500: 刪除失敗
        """
        from fastapi import HTTPException
        from sqlalchemy import text as _text
        from app.models.resource import Resource

        try:
            rid = uuid.UUID(resource_id)
        except ValueError:
            raise HTTPException(status_code=400, detail={"message": "resource_id 格式無效"})

        # 先撈 resource（不過濾 user_id）；若非擁有者改走 soft-hide 路徑
        resource = self.db.query(Resource).filter(Resource.id == rid).first()
        if resource is None:
            raise HTTPException(status_code=404, detail={"message": "資源不存在"})

        actor_uuid = uuid.UUID(user_id)
        if resource.user_id != actor_uuid:
            # 非擁有者 → soft hide（避免知識庫列表混入別人的孤兒，但不真正刪資料）
            from app.models.user_hidden_resource import UserHiddenResource
            from datetime import datetime as _dt, timezone as _tz
            existing = self.db.query(UserHiddenResource).filter_by(
                user_id=actor_uuid, resource_id=rid,
            ).first()
            if existing is None:
                self.db.add(UserHiddenResource(
                    user_id=actor_uuid,
                    resource_id=rid,
                    hidden_at=_dt.now(_tz.utc),
                ))
                self.db.commit()
            return {
                "deleted": False,
                "hidden": True,
                "resource_id": resource_id,
                "cascade_count": {"user_hidden_resources": 1},
            }

        # 事前統計
        cascade_count = _count_cascade_for_resource(self.db, rid)
        gcs_path = resource.gcs_path

        try:
            # 清 orphan questions（防 ck_questions_has_parent）
            self.db.execute(
                _text("DELETE FROM questions WHERE exam_id IS NULL AND historical_exam_id IS NULL")
            )
            self.db.delete(resource)

            # 寫 admin_audit_logs（不可逆操作必留 audit）
            from app.models.audit_log import AdminAuditLog
            from app.core.permissions import AuditAction
            self.db.add(AdminAuditLog(
                admin_id=uuid.UUID(user_id),
                action=AuditAction.RESOURCE_HARD_DELETED,
                target_type="resource",
                target_id=rid,
                details={"cascade_count": cascade_count, "resource_name": getattr(resource, "name", None)},
            ))
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.exception("hard_delete_resource failed for resource_id=%s: %s", resource_id, exc)
            raise HTTPException(
                status_code=500,
                detail={"message": f"刪除失敗：{type(exc).__name__}: {str(exc)[:300]}"},
            )

        # 清 GCS 檔案（非阻斷性）
        if gcs_path:
            try:
                from app.services.storage_service import get_storage_service
                get_storage_service().delete_file(gcs_path)
            except Exception as exc:
                logger.warning("GCS delete failed for %s: %s", gcs_path, exc)

        logger.info(
            "hard_delete_resource completed: resource_id=%s by user=%s cascade=%s",
            resource_id,
            user_id,
            cascade_count,
        )
        return {
            "deleted": True,
            "resource_id": resource_id,
            "cascade_count": cascade_count,
        }
