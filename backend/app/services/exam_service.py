"""Exam Configuration service — business logic for 04 測驗設定."""

import uuid

from sqlalchemy.orm import Session

from app.models.exam import Exam, ExamStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource
from app.models.user import User


class ExamService:

    def __init__(self, db: Session):
        self.db = db

    def submit_config(self, node_ids: list[str], question_count: int,
                      user_id: str, difficulty_distribution: dict | None = None) -> dict:
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

        # 先檢查可出題數限制
        if question_count > total_capacity:
            return {
                "error": True, "status_code": 400,
                "message": f"所選範圍最多可出 {total_capacity} 題，請調整題數",
            }

        # 再檢查方案限制
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

        # 取得 subject_id（從節點的資源取得）
        resource = self.db.query(Resource).filter_by(id=nodes[0].resource_id).first()
        subject_id = resource.subject_id if resource else uuid.uuid4()

        # 計算預估考試時間（每題 1.5 分鐘，最少 15 分鐘）
        duration_minutes = max(15, int(question_count * 1.5))

        # 將 node_ids 存入 difficulty_distribution 供 AI 生成使用
        exam_config = dict(difficulty_distribution or {})
        exam_config["node_ids"] = node_ids

        # 建立測驗
        exam = Exam(
            user_id=uid,
            subject_id=subject_id,
            status=ExamStatus.PENDING,
            total_questions=question_count,
            duration_minutes=duration_minutes,
            difficulty_distribution=exam_config,
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)

        return {
            "error": False,
            "exam_id": str(exam.id),
            "total_questions": question_count,
            "status": "PENDING",
            "sse_enabled": True,
        }
