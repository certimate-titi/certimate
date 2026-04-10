"""MCP Server request/response types and base definitions."""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import json


class MCPErrorType(str, Enum):
    """MCP error types."""
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"
    UNAUTHORIZED = "unauthorized"


@dataclass
class MCPResponse:
    """Standardized MCP response format."""
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class MCPError:
    """MCP error representation."""
    error_type: MCPErrorType
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "type": self.error_type.value,
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        return result


# ============================================================================
# Context Server Request/Response Types
# ============================================================================

@dataclass
class CoachContext:
    """Structured learning context for AI Coach."""
    user_id: str
    weak_areas: List[Dict[str, Any]]  # [{"topic": "代數", "error_rate": 0.45, "count": 12}, ...]
    mastery_scores: Dict[str, float]  # {"代數": 0.55, "幾何": 0.72, ...}
    recent_errors: List[Dict[str, Any]] = field(default_factory=list)  # Last N errors with context
    learning_style: Optional[Dict[str, Any]] = None  # Visual/kinesthetic/analytical preference
    learning_streak: int = 0
    total_questions_attempted: int = 0
    average_confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WeakAreaDetail:
    """Detailed weak area analysis."""
    topic: str
    error_rate: float
    total_attempts: int
    error_count: int
    misconceptions: List[str] = field(default_factory=list)
    common_wrong_answers: List[Dict[str, Any]] = field(default_factory=list)
    last_attempt_date: Optional[str] = None
    confidence_gap: float = 0.0  # Gap between confidence and actual correctness


@dataclass
class LearningStyle:
    """User learning style preferences."""
    preferred_modality: str  # "visual", "kinesthetic", "analytical", "auditory"
    optimal_spacing_days: int  # Ebbinghaus curve: 1, 3, 7, 14, 30...
    preferred_explanation_style: str  # "detailed", "concise", "example-driven"
    learning_pace: str  # "slow", "medium", "fast"


# ============================================================================
# Recommendation Server Request/Response Types
# ============================================================================

@dataclass
class RecommendedQuestion:
    """Recommended question with reasoning."""
    question_id: str
    topic: str
    difficulty_level: int  # 1-10 scale
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    reason: str  # Why this is recommended
    mastery_score: float  # 0-1, user's current mastery
    spacing_days: int  # Days since last attempt (Ebbinghaus)
    prerequisite_ready: bool  # Are prerequisites mastered?
    confidence_calibration_ready: bool  # Should user calibrate confidence?


@dataclass
class SpacingCalculation:
    """Spaced repetition calculation result."""
    next_review_date: str  # ISO 8601 date
    days_from_today: int
    ebbinghaus_interval: int  # 1, 3, 7, 14, 30, 60...
    reasoning: str  # Why this interval
    confidence_factor: float  # Adjusted interval based on confidence


@dataclass
class LearningPathItem:
    """Item in a learning path."""
    topic: str
    concept_id: str
    prerequisites: List[str] = field(default_factory=list)
    difficulty: int = 5
    estimated_hours: float = 1.0
    is_prerequisite_met: bool = False
    mastery_progress: float = 0.0


@dataclass
class NodeQualityValidation:
    """Knowledge node quality validation result."""
    is_valid: bool
    issues: List[Dict[str, Any]] = field(default_factory=list)  # [{"type": "missing_examples", "severity": "high"}, ...]
    score: float = 1.0  # 0-1 quality score
    recommendations: List[str] = field(default_factory=list)


# ============================================================================
# Data Fetching Server Request/Response Types
# ============================================================================

@dataclass
class DocumentChunk:
    """Document chunk with source tracking."""
    chunk_id: str
    content: str
    source_doc_id: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructuredKnowledgeNode:
    """Structured knowledge node extracted from document."""
    concept_name: str
    definition: str
    examples: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    prerequisite_concepts: List[str] = field(default_factory=list)
    bloom_level: str = "understand"  # remember, understand, apply...
    source_doc_id: str = ""
    source_page: Optional[int] = None


@dataclass
class UserDataBatch:
    """Batch of user data."""
    user_id: str
    mastery_scores: Dict[str, float]
    recent_answers: List[Dict[str, Any]] = field(default_factory=list)
    learning_preferences: Optional[Dict[str, Any]] = None
    subscription_info: Optional[Dict[str, Any]] = None


@dataclass
class CompressedChatHistory:
    """Compressed chat history."""
    session_id: str
    original_message_count: int
    compressed_message_count: int
    context_summary: str  # High-level summary of conversation
    last_messages: List[Dict[str, Any]] = field(default_factory=list)  # Last N messages in full


@dataclass
class RelationshipGraph:
    """Knowledge concept relationship graph."""
    concept_id: str
    concept_name: str
    prerequisites: List[Dict[str, Any]] = field(default_factory=list)  # [{"id": "...", "name": "..."}, ...]
    reinforces: List[Dict[str, Any]] = field(default_factory=list)  # Related concepts
    prerequisites_mastery: Dict[str, float] = field(default_factory=dict)  # concept_id -> mastery_score


# ============================================================================
# Caching types
# ============================================================================

@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    key: str
    value: Any
    ttl_seconds: int
    created_at: str  # ISO 8601 timestamp


# ============================================================================
# Common error responses
# ============================================================================

def error_response(
    error_type: MCPErrorType,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> MCPResponse:
    """Create a standardized error response."""
    return MCPResponse(
        success=False,
        error={
            "type": error_type.value,
            "message": message,
            "details": details or {}
        }
    )


def success_response(data: Any) -> MCPResponse:
    """Create a standardized success response."""
    return MCPResponse(success=True, data=data)
