"""考試結算任務 — V3 有機生長版（取代 V4 SM-2）.

流程：
1. 收到 exam_payload（user_id + answers）
2. 依序透過 OrganicProgressEngine 更新每個節點 progress
3. 向上傳播父節點 progress
4. 更新考試狀態為 SUBMITTED
"""

import logging
import uuid
from datetime import datetime, timezone

from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def settle_exam(self, exam_id: str, user_id: str, answers: list[dict]):
    """非同步結算考試（V3 有機生長）。"""
    try:
        _settle_exam_sync(exam_id, user_id, answers)
    except Exception as exc:
        logger.error("Exam settlement failed for %s: %s", exam_id, exc, exc_info=True)
        raise self.retry(exc=exc)


def _settle_exam_sync(exam_id: str, user_id: str, answers: list[dict]):
    """同步結算（也作為 Celery 不可用時的 fallback）。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    from app.models.exam import Exam, ExamStatus
    from app.services.organic_progress import OrganicProgressEngine

    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        progress_engine = OrganicProgressEngine(db)
        uid = uuid.UUID(user_id)
        eid = uuid.UUID(exam_id)

        # 取得考試科目的知識節點（用於 fallback 分配）
        exam_obj = db.query(Exam).filter(Exam.id == eid).first()
        fallback_nodes = []
        if exam_obj and exam_obj.subject_id:
            from app.models.knowledge_node import KnowledgeNode
            fallback_nodes = db.query(KnowledgeNode).filter(
                KnowledgeNode.subject_id == exam_obj.subject_id,
                KnowledgeNode.depth == 2,  # 只取葉節點
            ).all()

        # 1. 逐題更新 progress（考試權重 1.0）
        updated_nodes = set()
        fallback_idx = 0
        for ans in answers:
            nid = ans.get("node_id")
            # 無 node_id 時，用考試科目的葉節點輪流分配
            if not nid and fallback_nodes:
                nid = str(fallback_nodes[fallback_idx % len(fallback_nodes)].id)
                fallback_idx += 1
            if not nid:
                continue
            progress_engine.update_on_answer(
                user_id=user_id,
                node_id=nid,
                is_correct=ans.get("is_correct", False),
                weight=1.0,  # 考試權重 = 1.0（練習 = 0.5）
            )
            updated_nodes.add(nid)

        # 2. 向上傳播所有受影響的節點
        for nid in updated_nodes:
            progress_engine.propagate_upward(user_id, nid)

        # 3. 更新考試狀態
        exam = db.query(Exam).filter(Exam.id == eid).first()
        if exam:
            exam.status = ExamStatus.SUBMITTED
            exam.submitted_at = datetime.now(timezone.utc)

        db.commit()
        logger.info("Exam %s settled (V3): %d nodes updated", exam_id, len(updated_nodes))

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
