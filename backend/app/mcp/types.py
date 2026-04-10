"""
MCP (Model Context Protocol) 的类型定义
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID


@dataclass
class MCPRequest:
    """MCP 请求基类"""
    function: str
    params: dict[str, Any]
    user_id: Optional[UUID] = None


@dataclass
class MCPResponse:
    """MCP 响应基类"""
    status: str  # "success" | "error"
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Context Server 相关类型

@dataclass
class WeakArea:
    """弱点分析 - 单个知识点的掌握情况"""
    topic: str
    mastery: float  # 0.0 - 1.0
    error_count: int
    error_patterns: list[str] = field(default_factory=list)


@dataclass
class UserContext:
    """用户学习上下文 - 用于AI Coach"""
    user_id: UUID
    display_name: str
    weak_areas: list[WeakArea]  # 最弱的3个知识点
    recent_errors: list[dict] = field(default_factory=list)  # 最近的错误
    learning_style: str = "hybrid"  # visual, kinesthetic, analytical, hybrid
    daily_study_minutes: int = 30
    total_questions_answered: int = 0
    average_accuracy: float = 0.0


@dataclass
class LearningStyle:
    """学习风格"""
    visual_preference: float  # 0.0 - 1.0
    kinesthetic_preference: float  # 0.0 - 1.0
    analytical_preference: float  # 0.0 - 1.0
    optimal_spacing_interval: int  # 天数，基于艾宾浩斯遗忘曲线
    preferred_explanation_type: str  # "brief", "detailed", "with_examples"


# Recommendation Server 相关类型

@dataclass
class Question:
    """推荐的问题"""
    id: UUID
    text: str
    difficulty: float  # 0.0 - 1.0
    topic: str
    bloom_level: int  # 1-6，Bloom分类学
    mastery_required: float  # 前置条件掌握度
    last_answered_at: Optional[str] = None
    user_accuracy: float = 0.0


@dataclass
class RecommendedQuestions:
    """问题推荐结果"""
    user_id: UUID
    questions: list[Question]
    reasoning: str  # 推荐理由


@dataclass
class SpacedRepetitionTiming:
    """艾宾浩斯间隔复习时间"""
    question_id: UUID
    next_review_at: str  # ISO 8601 时间戳
    days_interval: int  # 距离现在的天数
    repetition_count: int  # 已复习次数


@dataclass
class NodeQualityValidation:
    """知识节点质量验证结果"""
    node_id: UUID
    is_valid: bool
    issues: list[str] = field(default_factory=list)  # 质量问题列表
    score: float = 1.0  # 0.0 - 1.0


# Data Fetching Server 相关类型

@dataclass
class DocumentChunk:
    """文档块 - 用于RAG"""
    document_id: UUID
    chunk_index: int
    text: str
    source_page: Optional[int] = None
    source_section: Optional[str] = None


@dataclass
class KnowledgeNodeData:
    """知识节点数据"""
    concept: str
    definition: str
    examples: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)  # {concept, relation_type}
