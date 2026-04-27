"""When — Rerank / Schema / env-var commands for Q1-Q4 補強."""

import importlib
import uuid
from unittest.mock import patch

from behave import when


@when('系統請求 top_k={k:d} 的檢索')
def step_retrieve_topk(context, k):
    from app.services.retrieval_service import RetrievalService
    from app.services.embedding_service import EmbeddingService

    # Force-reinstantiate to pick up RETRIEVAL_RERANK_ENABLED env
    svc = RetrievalService(context.db_session)
    resource_id = uuid.UUID(context.memo["rerank_resource_id"])

    # Replace embed_query with deterministic output
    svc.embedding_service.embed_query = lambda q: [0.1] * 1024  # type: ignore

    # Track rerank API calls
    original_rerank = svc.embedding_service.rerank
    call_count = {"n": 0}

    def spy_rerank(query, documents, top_k):
        call_count["n"] += 1
        if context.memo.get("_rerank_will_fail"):
            raise RuntimeError("simulated rerank failure")
        # Return top_k as-is
        return [
            {"index": i, "relevance_score": 1.0 - i * 0.1}
            for i in range(min(top_k, len(documents)))
        ]

    svc.embedding_service.rerank = spy_rerank  # type: ignore
    try:
        results = svc.retrieve(
            query="test query",
            resource_ids=[resource_id],
            top_k=k,
        )
        context.memo["retrieve_results"] = results
    finally:
        svc.embedding_service.rerank = original_rerank  # type: ignore

    context.memo["rerank_call_count"] = call_count["n"]


@when('系統重新載入 unified_knowledge_extraction_service 模組')
def step_reload_unified_module(context):
    import app.services.unified_knowledge_extraction_service as m
    importlib.reload(m)
    context.memo["reloaded_gemini_model"] = m.GEMINI_MODEL


@when('系統檢視 unified_knowledge_extraction._call_gemini 的 response_schema')
def step_inspect_response_schema(context):
    # We re-run the _call_gemini setup logic to capture the schema dict.
    # Since the schema is defined inline in the method, inspect source.
    import inspect
    import app.services.unified_knowledge_extraction_service as m
    source = inspect.getsource(m.UnifiedKnowledgeExtractionService._call_gemini_inner)
    # Record for assertion: source must contain maxItems: 6
    context.memo["call_gemini_source"] = source


@when('系統呼叫 _call_gemini')
def step_call_gemini_with_schema_fail(context):
    """Simulate Gemini rejecting response_schema and retrying without it."""
    from unittest.mock import MagicMock, patch
    import app.services.unified_knowledge_extraction_service as m

    # Build a minimal service instance
    svc = m.UnifiedKnowledgeExtractionService(context.db_session)

    # Mock the module-level _gemini_client
    mock_client = MagicMock()
    # First call (with schema) raises, second call (without schema) succeeds
    mock_response = MagicMock()
    mock_response.text = '{"knowledge_tree": {"chapters": []}}'
    mock_client.models.generate_content.side_effect = [
        Exception("INVALID_ARGUMENT: response_schema rejected"),
        mock_response,
    ]

    # Capture warnings
    warnings: list[str] = []
    original_warning = m.log.warning

    def capture_warning(msg, *args, **kwargs):
        formatted = msg % args if args else msg
        warnings.append(str(formatted))
        original_warning(msg, *args, **kwargs)

    with patch.object(m, "_gemini_client", mock_client), \
         patch.object(m.log, "warning", side_effect=capture_warning):
        try:
            result = svc._call_gemini("test prompt")
            context.memo["call_gemini_result"] = result
        except Exception as e:
            context.memo["call_gemini_error"] = str(e)
    context.memo["call_gemini_warnings"] = warnings
    context.memo["call_gemini_call_count"] = mock_client.models.generate_content.call_count
