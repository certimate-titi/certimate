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

        # 防止連點重複建立：檢查是否有相同配置的 PENDING/READY 測驗
        pending_exam = (
            self.db.query(Exam)
            .filter(Exam.user_id == uid)
            .filter(Exam.status.in_([ExamStatus.PENDING, ExamStatus.READY]))
            .filter(Exam.total_questions == question_count)
            .order_by(Exam.created_at.desc())
            .first()
        )
        if pending_exam and pending_exam.difficulty_distribution:
            existing_nodes = set(pending_exam.difficulty_distribution.get("node_ids", []))
            if existing_nodes == set(node_ids):
                return {
                    "error": True, "status_code": 409,
                    "message": "已有相同配置的測驗正在準備中，請勿重複建立",
                }

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
            from app.models.question import Question as QuestionModel
            from sqlalchemy import func as sa_func

            # 從使用者選擇的知識節點 → 找出對應的 resource → subject → 考古題
            # Step 1: 收集所有相關的 resource_ids 和 subject_ids
            selected_resource_ids = set()
            selected_subject_ids = set()
            for n in nodes:
                if n.resource_id:
                    selected_resource_ids.add(n.resource_id)
                    res = self.db.query(Resource).filter_by(id=n.resource_id).first()
                    if res and res.subject_id:
                        selected_subject_ids.add(res.subject_id)
                if hasattr(n, 'subject_id') and n.subject_id:
                    selected_subject_ids.add(n.subject_id)

            # Step 2: 找出同 subject 下的 historical_exam_ids
            from app.models.historical_exam import HistoricalExam
            he_query = self.db.query(HistoricalExam.id)

            # 如果有 subject 關聯，用 subject 的 code/name 來匹配
            if selected_subject_ids:
                subjects_for_match = self.db.query(Subject).filter(
                    Subject.id.in_(selected_subject_ids)
                ).all()
                # 科目隔離規則：用 exam_subject_codes 精確匹配，不用模糊名稱
                from sqlalchemy import or_, and_
                code_filters = []
                for s in subjects_for_match:
                    if s.exam_subject_codes:
                        for code in s.exam_subject_codes:
                            parts = code.split(":", 1)
                            if len(parts) == 2:
                                code_filters.append(and_(
                                    HistoricalExam.exam_code == parts[0],
                                    HistoricalExam.subject_code == parts[1],
                                ))
                # Fallback: 用完整 subject_name 精確匹配（不截斷）
                if not code_filters:
                    subject_names = [s.name for s in subjects_for_match]
                    name_filters = [HistoricalExam.subject_name == name for name in subject_names if name]
                    if name_filters:
                        he_query = he_query.filter(or_(*name_filters))
                else:
                    he_query = he_query.filter(or_(*code_filters))

            matching_he_ids = [row[0] for row in he_query.all()]

            # Step 3: 從匹配的 historical_exams 抽取考古題
            q_query = (
                self.db.query(QuestionModel)
                .filter(QuestionModel.historical_exam_id.isnot(None))
                .filter(QuestionModel.correct_answer.isnot(None))
                .filter(QuestionModel.correct_answer != '')
            )

            if matching_he_ids:
                q_query = q_query.filter(QuestionModel.historical_exam_id.in_(matching_he_ids))

            historical_questions = (
                q_query
                .order_by(sa_func.random())
                .limit(question_count)
                .all()
            )

            # 科目隔離規則：禁止全域 fallback，無匹配考古題時回傳錯誤
            # （已移除舊的全題庫隨機抽取 fallback）

            actual_count = len(historical_questions)
            hint = ""
            if actual_count < question_count:
                hint = f"此範圍考古題僅 {actual_count} 題，已自動調整"
            if actual_count == 0:
                return {"error": True, "status_code": 400, "message": "找不到可用的考古題"}

            # Get subject_id — 從節點的 subject_id 直接取，不 fallback 到隨機科目
            subject_id = None
            for n in nodes:
                if n.subject_id:
                    subject_id = n.subject_id
                    break
                if n.resource_id:
                    res = self.db.query(Resource).filter_by(id=n.resource_id).first()
                    if res and res.subject_id:
                        subject_id = res.subject_id
                        break
            if not subject_id:
                return {"error": True, "status_code": 400, "message": "無法判斷考試科目，請重新選擇知識範圍"}

            exam = Exam(
                user_id=uid,
                subject_id=subject_id,
                status=ExamStatus.READY,  # READY = 題目已抽好
                total_questions=actual_count,
                duration_minutes=max(15, int(actual_count * 1.5)),
                difficulty_distribution=difficulty_distribution,
                historical_priority=True,
            )
            self.db.add(exam)
            self.db.flush()

            # 將考古題複製到此考試（更新 exam_id）
            # 科目隔離：node_id 必須指向考試科目的節點，不能跨科目
            exam_node_ids = {
                str(kn.id) for kn in
                self.db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == subject_id).all()
            }
            for i, hq in enumerate(historical_questions):
                # 驗證 node_id 屬於考試科目，否則清空
                safe_node_id = hq.node_id if (hq.node_id and str(hq.node_id) in exam_node_ids) else None
                new_q = QuestionModel(
                    id=uuid.uuid4(),
                    exam_id=exam.id,
                    historical_exam_id=None,  # 考試題目為副本，不共用 (he_id, q_num) 唯一索引
                    node_id=safe_node_id,
                    question_number=i + 1,
                    type=hq.type,
                    difficulty=hq.difficulty,
                    content=hq.content,
                    option_a=hq.option_a,
                    option_b=hq.option_b,
                    option_c=hq.option_c,
                    option_d=hq.option_d,
                    correct_answer=hq.correct_answer,
                    explanation=hq.explanation,
                    figure_urls=list(hq.figure_urls or []),
                    figure_description=hq.figure_description,
                    bloom_category=hq.bloom_category,
                    historical_source=hq.historical_source,
                    source_type="historical",
                    quality_flag="ok",
                    tenant_id=hq.tenant_id,
                )
                self.db.add(new_q)

            self.db.commit()
            self.db.refresh(exam)

            response = {
                "error": False,
                "exam_id": str(exam.id),
                "total_questions": actual_count,
                "status": "READY",
                "sse_enabled": False,
                "bloom_source": "historical",
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

        # --- Determine subject_id — 從節點的 subject_id 直接取，不 fallback 到隨機科目 ---
        subject_id = None
        for n in nodes:
            if n.subject_id:
                subject_id = n.subject_id
                break
            if n.resource_id:
                res = self.db.query(Resource).filter_by(id=n.resource_id).first()
                if res and res.subject_id:
                    subject_id = res.subject_id
                    break
        if not subject_id:
            return {"error": True, "status_code": 400, "message": "無法判斷考試科目，請重新選擇知識範圍"}

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
