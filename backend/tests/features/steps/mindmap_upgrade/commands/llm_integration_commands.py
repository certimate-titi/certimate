"""When — LLM-integration 命令步驟 (mindmap upgrade Feature 34).

使用 unittest.mock.patch 攔截 _call_gemini_inner，避免觸發真實 API。
"""

from unittest.mock import patch

from behave import when

from tests.features.steps.mindmap_upgrade.aggregate_given.llm_integration_setup import (
    _build_mock_gemini_response,
    CHAPTER_NAMES,
)


@when('系統對 "{subject_name}" 執行 UnifiedKnowledgeExtractionService.extract()')
def step_impl_run_extract_with_syllabus(context, subject_name):
    """以 mock Gemini 回應執行 extract()，回應章名與 syllabus_topics 對齊。"""
    from app.services import unified_knowledge_extraction_service as ukes_module
    from app.services.unified_knowledge_extraction_service import (
        UnifiedKnowledgeExtractionService,
    )

    sid = context.memo["llm_subject_id"]
    chapter_names = context.memo.get("syllabus_chapter_names", CHAPTER_NAMES[:6])
    mock_tree = _build_mock_gemini_response(chapter_names)

    with patch.object(
        ukes_module.UnifiedKnowledgeExtractionService,
        "_call_gemini_inner",
        return_value=mock_tree,
    ):
        svc = UnifiedKnowledgeExtractionService(context.db_session)
        result = svc.extract(sid)

    context.memo["extract_result"] = result


@when('系統對該科目執行 extract() 含 Voyage 語意映射')
def step_impl_run_extract_with_voyage(context):
    """以 mock Gemini + mock Voyage 執行 extract()，驗證 weak-keyword fallback 路徑。"""
    from app.services import unified_knowledge_extraction_service as ukes_module
    from app.services.unified_knowledge_extraction_service import (
        UnifiedKnowledgeExtractionService,
    )

    sid = context.memo["voyage_subject_id"]
    node_names = context.memo["voyage_node_names"]
    weak_count = context.memo.get("voyage_weak_q_count", 5)

    mock_tree = _build_mock_gemini_response(node_names)

    # Voyage semantic fallback: each weak question maps to first node
    first_node_name = node_names[0] if node_names else "節點1"

    def _fake_voyage_map(self_svc, subject_id, leaf_tuples, weak_questions):
        """Replace voyage API calls: maps all weak questions to first leaf node."""
        from sqlalchemy import text as sa_text
        first_nid = leaf_tuples[0][0] if leaf_tuples else None
        if first_nid is None:
            return 0
        for q in weak_questions:
            self_svc.db.execute(
                sa_text("UPDATE questions SET node_id = :nid WHERE id = :qid"),
                {"nid": first_nid, "qid": q[0]},
            )
        return len(weak_questions)

    with (
        patch.object(
            ukes_module.UnifiedKnowledgeExtractionService,
            "_call_gemini_inner",
            return_value=mock_tree,
        ),
        patch.object(
            ukes_module.UnifiedKnowledgeExtractionService,
            "_semantic_map_questions_via_voyage",
            _fake_voyage_map,
        ),
    ):
        svc = UnifiedKnowledgeExtractionService(context.db_session)
        result = svc.extract(sid)

    context.memo["extract_result"] = result
    context.memo["voyage_mock_handled"] = weak_count
