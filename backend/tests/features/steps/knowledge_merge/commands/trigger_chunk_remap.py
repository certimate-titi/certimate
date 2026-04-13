"""When 系統執行 chunk 到統一節點的映射 — Command"""

import uuid

from behave import when
from sqlalchemy import text


@when('系統執行 chunk 到統一節點的映射')
def step_trigger_chunk_remap(context):
    db = context.db_session
    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id，請先設定考科"

    sid = uuid.UUID(subject_id)

    # Directly call the remap method (unit-test style, no API needed)
    from app.services.unified_knowledge_extraction_service import (
        UnifiedKnowledgeExtractionService,
    )

    svc = UnifiedKnowledgeExtractionService(db)
    chunks_remapped = svc._remap_chunks_to_nodes(sid, question_keywords={})
    db.commit()

    context.memo["chunks_remapped"] = chunks_remapped
