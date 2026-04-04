"""Exam Configuration service — business logic for 04 測驗設定."""

import json
import uuid

from sqlalchemy.orm import Session

from app.models.exam import Exam, ExamStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceStatus
from app.models.subject import Subject
from app.models.user import User


DEFAULT_BLOOM = {
    "remember": 20,
    "understand": 25,
    "apply": 25,
    "analyze": 15,
    "evaluate": 10,
    "create": 5,
}


class ExamService:

    def __init__(self, db: Session):
        self.db = db

    def submit_config(self, node_ids: list[str], question_count: int,
                      user_id: str, difficulty_distribution: dict | None = None,
                      custom_bloom_ratio: dict | None = None,
                      question_types: list[str] | None = None,
                      exam_mode: str | None = None) -> dict:
        uid = uuid.UUID(user_id)

        # 驗證：至少選擇一個節點
        if not node_ids:
            return {"error": True, "status_code": 400, "message": "請至少選擇一個知識範圍"}

        # 查詢使用者
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan
        plan_val = plan.value if hasattr(plan, 'value') else plan

        # 查詢節點，計算可出題總數
        node_uuids = [uuid.UUID(nid) for nid in node_ids]
        nodes = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.id.in_(node_uuids)
        ).all()

        total_capacity = sum(n.available_questions or 0 for n in nodes)

        # If no pre-set capacity but nodes exist, allow AI generation (default 5 per node)
        if total_capacity == 0 and nodes:
            total_capacity = len(nodes) * 5

        # --- Custom Bloom validation (before question count checks) ---
        bloom_source = "default"
        bloom_distribution = None
        hint = None

        if custom_bloom_ratio:
            if plan_val == "ULTRA":
                total_pct = sum(custom_bloom_ratio.values())
                if total_pct != 100:
                    return {"error": True, "status_code": 400,
                            "message": "Bloom 比例加總必須為 100%"}
                bloom_source = "custom"
                bloom_distribution = custom_bloom_ratio
            else:
                bloom_source = "default"
                hint = "Bloom 自訂比例為 ULTRA 方案專屬功能"

        # --- Handle historical_only exam mode ---
        if exam_mode == "historical_only":
            available = sum(n.available_questions or 0 for n in nodes)
            actual_count = question_count
            if question_count > available:
                hint = f"此範圍考古題僅 {available} 題，已自動調整"
                actual_count = available

            # Build stub historical questions
            questions = [
                {"id": str(uuid.uuid4()), "reliability": "green"}
                for _ in range(actual_count)
            ]

            # Get subject_id for exam record
            resource = self.db.query(Resource).filter_by(id=nodes[0].resource_id).first() if nodes else None
            if resource and resource.subject_id:
                subject_id = resource.subject_id
            else:
                # Try to find a valid subject
                subject = self.db.query(Subject).first()
                subject_id = subject.id if subject else uuid.uuid4()

            exam = Exam(
                user_id=uid,
                subject_id=subject_id,
                status=ExamStatus.PENDING,
                total_questions=actual_count,
                duration_minutes=max(15, int(actual_count * 1.5)),
                difficulty_distribution=difficulty_distribution,
                historical_priority=True,
            )
            self.db.add(exam)
            self.db.commit()
            self.db.refresh(exam)

            response = {
                "error": False,
                "exam_id": str(exam.id),
                "total_questions": actual_count,
                "status": "PENDING",
                "sse_enabled": True,
                "bloom_source": "historical",
                "questions": questions,
                "ai_generated_count": 0,
            }
            if hint:
                response["hint"] = hint
            return response

        # --- Question count validation ---
        if question_count > total_capacity:
            return {
                "error": True, "status_code": 400,
                "message": f"所選範圍最多可出 {total_capacity} 題，請調整題數",
            }

        # Plan limits
        plan_limits = {
            "FREE": 10,
            "PRO": 50,
            "PRO_PLUS": 100,
            "ULTRA": 999,
        }
        limit = plan_limits.get(plan_val, 10)

        if question_count > limit:
            upgrade_msgs = {
                "FREE": "FREE 方案每次測驗最多 10 題，升級 PRO 最多可出 50 題",
                "PRO": "PRO 方案每次測驗最多 50 題，升級 ULTRA 最多可出 100 題以上",
            }
            msg = upgrade_msgs.get(plan_val, f"方案限制每次最多 {limit} 題")
            return {"error": True, "status_code": 400, "message": msg}

        # --- Determine subject_id ---
        resource = self.db.query(Resource).filter_by(id=nodes[0].resource_id).first() if nodes else None
        subject_id = resource.subject_id if resource else uuid.uuid4()

        # --- Auto-detect bloom_source (if not already set by custom bloom) ---
        if bloom_source == "default" and not custom_bloom_ratio:
            subject = self.db.query(Subject).filter_by(id=subject_id).first()
            if subject and subject.description:
                try:
                    desc_data = json.loads(subject.description)
                    if "bloom_stats" in desc_data:
                        bloom_source = "historical"
                except (json.JSONDecodeError, TypeError):
                    pass

        # --- Calculate historical_ratio ---
        historical_ratio = 70 if plan_val == "ULTRA" else 30

        # --- Build exam config ---
        exam_config = dict(difficulty_distribution or {})
        exam_config["node_ids"] = node_ids

        duration_minutes = max(15, int(question_count * 1.5))

        exam = Exam(
            user_id=uid,
            subject_id=subject_id,
            status=ExamStatus.PENDING,
            total_questions=question_count,
            duration_minutes=duration_minutes,
            difficulty_distribution=exam_config,
            custom_bloom_ratio=custom_bloom_ratio if bloom_source == "custom" else None,
            historical_priority=plan_val == "ULTRA",
            question_types=question_types,
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)

        response = {
            "error": False,
            "exam_id": str(exam.id),
            "total_questions": question_count,
            "status": "PENDING",
            "sse_enabled": True,
            "bloom_source": bloom_source,
            "historical_ratio": historical_ratio,
        }

        if bloom_distribution:
            response["bloom_distribution"] = bloom_distribution
        if hint:
            response["hint"] = hint
        if question_types:
            response["question_types"] = question_types

        # Return clean difficulty distribution (without internal fields)
        if difficulty_distribution:
            clean_diff = {k: v for k, v in difficulty_distribution.items()
                         if k not in ("exam_mode", "node_ids")}
            if clean_diff:
                response["difficulty_distribution"] = clean_diff

        return response

    def select_resource(self, user_id: str, resource_id: str) -> dict:
        """Validate resource can be used for exam."""
        rid = uuid.UUID(resource_id)
        resource = self.db.query(Resource).filter_by(id=rid).first()
        if not resource:
            return {"error": True, "status_code": 404, "message": "Not Found"}

        if resource.status != ResourceStatus.COMPLETED:
            return {"error": True, "status_code": 400,
                    "message": "該文件尚未處理完成，無法用於出題"}

        return {"error": False, "resource_id": str(resource.id), "status": resource.status.value}
