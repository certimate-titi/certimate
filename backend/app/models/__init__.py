"""SQLAlchemy ORM Models。

Base 是所有 Model 的基類，用於 Alembic 自動偵測 schema 變更。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy ORM Base Class。"""
    pass


from app.models.user import User  # noqa: F401, E402
from app.models.subject import SubjectCategory, Subject  # noqa: F401, E402
from app.models.institution import Institution  # noqa: F401, E402
from app.models.learning_journey import LearningJourney  # noqa: F401, E402
from app.models.resource import Resource  # noqa: F401, E402
from app.models.subject_default_resource import SubjectDefaultResource  # noqa: F401, E402
from app.models.knowledge_node import KnowledgeNode  # noqa: F401, E402
from app.models.node_mastery import NodeMastery  # noqa: F401, E402
from app.models.ai_chat import AiChatSession, AiChatMessage  # noqa: F401, E402
from app.models.ai_cooldown import AiCooldown  # noqa: F401, E402
from app.models.plan_quota import PlanQuota  # noqa: F401, E402
from app.models.exam import Exam  # noqa: F401, E402
from app.models.question import Question  # noqa: F401, E402
from app.models.answer import Answer  # noqa: F401, E402
from app.models.invoice import Invoice  # noqa: F401, E402
from app.models.question_stat import QuestionStat  # noqa: F401, E402
from app.models.audit_log import AdminAuditLog  # noqa: F401, E402
from app.models.ai_usage_ledger import AiUsageLedger  # noqa: F401, E402
from app.models.budget_config import BudgetConfig  # noqa: F401, E402
from app.models.budget_alert_log import BudgetAlertLog  # noqa: F401, E402
from app.models.content_report import ContentReport  # noqa: F401, E402
from app.models.transaction import Transaction  # noqa: F401, E402
from app.models.refund import Refund  # noqa: F401, E402
from app.models.coupon import Coupon  # noqa: F401, E402
from app.models.ai_model_routing import AiModelRouting  # noqa: F401, E402
from app.models.system_announcement import SystemAnnouncement  # noqa: F401, E402
from app.models.feature_flag import FeatureFlag  # noqa: F401, E402
from app.models.prompt_template import PromptTemplate, PromptTemplateHistory  # noqa: F401, E402
from app.models.user_usage import UserUsage  # noqa: F401, E402
from app.models.feedback import Feedback, FeedbackAttachment  # noqa: F401, E402
from app.models.weekly_report import WeeklyReport  # noqa: F401, E402
from app.models.anomaly_record import AnomalyRecord  # noqa: F401, E402
from app.models.maintenance_task import MaintenanceTask  # noqa: F401, E402
from app.models.maintenance_schedule import MaintenanceSchedule  # noqa: F401, E402
from app.models.maintenance_notification import MaintenanceNotification  # noqa: F401, E402
from app.models.resource_chunk import ResourceChunk  # noqa: F401, E402
from app.models.student_group import StudentGroup, StudentGroupMember  # noqa: F401, E402
from app.models.institution_assignment import InstitutionAssignment  # noqa: F401, E402
from app.models.early_warning_rule import EarlyWarningRule  # noqa: F401, E402
from app.models.reverse_engineering_task import ReverseEngineeringTask  # noqa: F401, E402
from app.models.merge_conflict import MergeConflict  # noqa: F401, E402
from app.models.merge_history import MergeHistory  # noqa: F401, E402
from app.models.tenant import Tenant  # noqa: F401, E402
from app.models.historical_exam import HistoricalExam  # noqa: F401, E402
from app.models.syllabus_topic import SyllabusTopic  # noqa: F401, E402
from app.models.import_task import ImportTask, ImportTaskStatus  # noqa: F401, E402
from app.models.daily_quest_progress import DailyQuestProgress  # noqa: F401, E402
from app.models.user_hidden_resource import UserHiddenResource  # noqa: F401, E402

__all__ = [
    "Base",
    "User",
    "SubjectCategory",
    "Subject",
    "Institution",
    "LearningJourney",
    "Resource",
    "KnowledgeNode",
    "NodeMastery",
    "AiChatSession",
    "AiChatMessage",
    "AiCooldown",
    "PlanQuota",
    "Exam",
    "Question",
    "Answer",
    "Invoice",
    "QuestionStat",
    "AdminAuditLog",
    "ContentReport",
    "Transaction",
    "Refund",
    "Coupon",
    "AiModelRouting",
    "SystemAnnouncement",
    "FeatureFlag",
    "PromptTemplate",
    "PromptTemplateHistory",
    "UserUsage",
    "Feedback",
    "FeedbackAttachment",
    "WeeklyReport",
    "AnomalyRecord",
    "MaintenanceTask",
    "MaintenanceSchedule",
    "MaintenanceNotification",
    "ResourceChunk",
    "StudentGroup",
    "StudentGroupMember",
    "InstitutionAssignment",
    "EarlyWarningRule",
    "ReverseEngineeringTask",
    "MergeConflict",
    "MergeHistory",
    "Tenant",
    "HistoricalExam",
    "SyllabusTopic",
    "ImportTask",
    "ImportTaskStatus",
    "DailyQuestProgress",
    "UserHiddenResource",
]
