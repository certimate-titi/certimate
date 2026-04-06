"""API 路由註冊。"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.resource import router as resource_router
from app.api.knowledge_map import router as knowledge_map_router
from app.api.exam import router as exam_router
from app.api.wrong_answer import router as wrong_answer_router
from app.api.subscription import router as subscription_router
from app.api.schedule import router as schedule_router
from app.api.b2b import router as b2b_router
from app.api.resource_library import router as resource_library_router
from app.api.onboarding import router as onboarding_router
from app.api.admin import router as admin_router
from app.api.admin_finance import router as admin_finance_router
from app.api.admin_moderation import router as admin_moderation_router
from app.api.admin_settings import router as admin_settings_router
from app.api.dashboard import router as dashboard_router
from app.api.subjects import router as subjects_router
from app.api.ecpay import router as ecpay_router
from app.api.feedback import router as feedback_router
from app.api.community import router as community_router
from app.api.anomaly import router as anomaly_router
from app.api.announcements import router as announcements_router
from app.api.ai_questions import router as ai_questions_router
from app.api.retirement import router as retirement_router
from app.api.learning_journey import router as learning_journey_router
from app.api.ai_chat import router as ai_chat_router
from app.api.pricing import router as pricing_router
from app.api.reverse_engineering import router as reverse_engineering_router
from app.api.wrong_answer_map import router as wrong_answer_map_router
from app.api.difficulty_progression import router as difficulty_progression_router
from app.api.knowledge_merge import router as knowledge_merge_router

router = APIRouter()

router.include_router(auth_router, tags=["auth"])
router.include_router(resource_router, tags=["resources"])
router.include_router(knowledge_map_router, tags=["knowledge-map"])
router.include_router(exam_router, tags=["exams"])
router.include_router(wrong_answer_router, tags=["wrong-answers"])
router.include_router(subscription_router, tags=["subscriptions"])
router.include_router(schedule_router, tags=["schedule"])
router.include_router(b2b_router, tags=["b2b"])
router.include_router(resource_library_router, tags=["resource-library"])
router.include_router(onboarding_router, tags=["onboarding"])
router.include_router(admin_router, tags=["admin"])
router.include_router(admin_finance_router, tags=["admin-finance"])
router.include_router(admin_moderation_router, tags=["admin-moderation"])
router.include_router(admin_settings_router, tags=["admin-settings"])
router.include_router(dashboard_router, tags=["dashboard"])
router.include_router(subjects_router, tags=["subjects"])
router.include_router(ecpay_router, tags=["ecpay"])
router.include_router(feedback_router, tags=["feedback"])
router.include_router(community_router, tags=["community"])
router.include_router(anomaly_router, tags=["anomaly"])
router.include_router(announcements_router, tags=["announcements"])
router.include_router(ai_questions_router, tags=["ai-questions"])
router.include_router(retirement_router, tags=["retirement"])
router.include_router(learning_journey_router, tags=["learning-journeys"])
router.include_router(ai_chat_router, tags=["ai-chat"])
router.include_router(pricing_router, tags=["pricing"])
router.include_router(reverse_engineering_router, tags=["reverse-engineering"])
router.include_router(wrong_answer_map_router, tags=["wrong-answer-map"])
router.include_router(difficulty_progression_router, tags=["difficulty-progression"])
router.include_router(knowledge_merge_router, tags=["knowledge-merge"])
