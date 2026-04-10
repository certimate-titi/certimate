"""MCP (Model Context Protocol) Server Package for CertiMate.

Provides structured access to:
- User context (mastery, weak areas, learning style)
- Intelligent recommendations (question selection, spacing)
- Data fetching (document chunks, knowledge extraction)
"""

from app.mcp.types import (
    MCPResponse,
    MCPError,
    MCPErrorType,
    CoachContext,
    WeakAreaDetail,
    LearningStyle,
    RecommendedQuestion,
    SpacingCalculation,
    LearningPathItem,
    NodeQualityValidation,
    DocumentChunk,
    StructuredKnowledgeNode,
    UserDataBatch,
    CompressedChatHistory,
    RelationshipGraph,
    CacheEntry,
    error_response,
    success_response,
)

from app.mcp.base_server import (
    BaseMCPServer,
    MCPServerFactory,
)

from app.mcp.context_server import ContextServer
from app.mcp.recommendation_server import RecommendationServer

__all__ = [
    # Types
    "MCPResponse",
    "MCPError",
    "MCPErrorType",
    "CoachContext",
    "WeakAreaDetail",
    "LearningStyle",
    "RecommendedQuestion",
    "SpacingCalculation",
    "LearningPathItem",
    "NodeQualityValidation",
    "DocumentChunk",
    "StructuredKnowledgeNode",
    "UserDataBatch",
    "CompressedChatHistory",
    "RelationshipGraph",
    "CacheEntry",
    "error_response",
    "success_response",
    # Server classes
    "BaseMCPServer",
    "MCPServerFactory",
    "ContextServer",
    "RecommendationServer",
]

__version__ = "1.0.0"
