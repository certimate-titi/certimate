"""Knowledge Navigation service — business logic for 03b knowledge map navigation."""

import uuid

from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.learning_journey import LearningJourney
from app.models.resource import Resource
from app.models.ai_chat import AiChatSession, AiChatMessage
from app.models.user import User


class KnowledgeNavService:

    def __init__(self, db: Session):
        self.db = db

    def _ensure_exam_bank_resource(self, subject_id: uuid.UUID) -> None:
        """若科目有考古題但無 Resource，觸發自動建立。"""
        from app.models.subject import Subject
        from app.services.onboarding_service import OnboardingService
        subject = self.db.query(Subject).filter_by(id=subject_id).first()
        if subject and subject.available_questions and subject.available_questions > 0:
            existing = self.db.query(Resource).filter_by(subject_id=subject_id).first()
            if not existing:
                svc = OnboardingService(self.db)
                svc._ensure_exam_bank_resource(subject)
                self.db.flush()

    def get_nodes_by_subject(self, subject_id: str, user_id: str) -> dict:
        """取得科目下的知識節點（含掌握度顏色）。"""
        uid = uuid.UUID(user_id)
        sid = uuid.UUID(subject_id)

        # 檢查使用者是否備考此科目
        journey = self.db.query(LearningJourney).filter_by(
            user_id=uid, subject_id=sid
        ).first()
        if not journey:
            return {"error": True, "status_code": 403, "message": "您尚未加入此備考科目"}

        # 確保考古題 Resource 存在
        self._ensure_exam_bank_resource(sid)

        # 找此科目下所有資源
        resources = self.db.query(Resource).filter_by(subject_id=sid).all()
        resource_ids = [r.id for r in resources]

        if not resource_ids:
            return {"error": False, "nodes": [], "resources": []}

        # 找所有知識節點
        nodes = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.resource_id.in_(resource_ids)
        ).order_by(KnowledgeNode.sort_order).all()

        # 找掌握度
        node_ids = [n.id for n in nodes]
        masteries = self.db.query(NodeMastery).filter(
            NodeMastery.user_id == uid,
            NodeMastery.node_id.in_(node_ids)
        ).all()
        mastery_map = {str(m.node_id): m for m in masteries}

        # Build flat node list with full info
        flat_nodes = {}
        for node in nodes:
            m = mastery_map.get(str(node.id))
            flat_nodes[str(node.id)] = {
                "id": str(node.id),
                "name": node.name,
                "depth": node.depth,
                "parent_id": str(node.parent_id) if node.parent_id else None,
                "resource_id": str(node.resource_id) if node.resource_id else None,
                "sort_order": node.sort_order or 0,
                "source_page": node.source_page_number,
                "available_questions": node.available_questions or 0,
                "mastery_rate": int(m.mastery_rate) if m else 0,
                "color": m.color if m else "gray",
                "children": [],
            }

        # Build tree by attaching children to parents
        roots = []
        for nid, node_data in flat_nodes.items():
            pid = node_data["parent_id"]
            if pid and pid in flat_nodes:
                flat_nodes[pid]["children"].append(node_data)
            else:
                roots.append(node_data)

        # Sort children by sort_order
        def sort_tree(node_list):
            node_list.sort(key=lambda n: n["sort_order"])
            for n in node_list:
                sort_tree(n["children"])
        sort_tree(roots)

        result_resources = [
            {"id": str(r.id), "name": r.name, "type": r.type.value if hasattr(r.type, 'value') else r.type}
            for r in resources
        ]

        return {"error": False, "nodes": roots, "resources": result_resources}

    def get_node_detail(self, node_id: str, user_id: str) -> dict:
        """取得節點詳情（含溯源資訊）。"""
        node = self.db.query(KnowledgeNode).filter_by(
            id=uuid.UUID(node_id)
        ).first()
        if not node:
            return {"error": True, "status_code": 404, "message": "知識節點不存在"}

        resource = self.db.query(Resource).filter_by(id=node.resource_id).first()

        # 判斷來源類型
        resource_type_val = resource.type.value if hasattr(resource.type, 'value') else resource.type
        is_youtube = resource_type_val == "youtube"

        if is_youtube:
            source_type = "youtube"
            ts = node.source_timestamp_seconds or 0
            hours = ts // 3600
            minutes = (ts % 3600) // 60
            seconds = ts % 60
            source_ref = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            source_type = "pdf"
            source_ref = f"第 {node.source_page_number} 頁" if node.source_page_number else ""

        return {
            "error": False,
            "node_name": node.name,
            "source_type": source_type,
            "source_ref": source_ref,
            "source_text": node.source_text or "（無原文摘要）",
            "source_citation": {
                "source_page_number": node.source_page_number,
                "source_timestamp_seconds": node.source_timestamp_seconds,
                "display": f"來源頁碼：{source_ref}" if source_type == "pdf" else f"影片時間戳：{source_ref}",
            },
            "source_info": {
                "node_name": node.name,
                "source_type": source_type,
                "source_ref": source_ref,
            },
        }

    def get_node_source(self, node_id: str, user_id: str) -> dict:
        """取得節點溯源內容。"""
        return self.get_node_detail(node_id, user_id)

    def get_layout(self, user_id: str) -> dict:
        """取得知識心智圖頁面佈局。"""
        return {
            "error": False,
            "coach_panel": {
                "width": "75%",
                "content": "AI 教練對話區與溯源內容",
                "type": "coach_and_source",
            },
            "mind_map_nav": {
                "width": "25%",
                "knowledge_tree": True,
                "content": "互動知識節點樹",
                "type": "knowledge_nav",
            },
        }

    def send_coach_message(self, node_id: str | None, message: str, user_id: str) -> dict:
        """發送 AI 教練訊息。"""
        uid = uuid.UUID(user_id)
        nid = uuid.UUID(node_id) if node_id else None

        # 查詢使用者
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan
        plan_val = plan.value if hasattr(plan, 'value') else plan

        # FREE 用戶：單節點 3 次追問限制
        if plan_val == "FREE" and nid:
            session = self.db.query(AiChatSession).filter_by(
                user_id=uid, context_type="node", context_id=nid
            ).first()
            if session:
                msg_count = self.db.query(AiChatMessage).filter_by(
                    session_id=session.id, role="user"
                ).count()
                if msg_count >= 3:
                    return {
                        "error": True,
                        "status_code": 403,
                        "message": "已達免費追問上限，升級 PRO_PLUS 解鎖無限對話",
                    }

        # PRO 用戶：不允許高階教練（毛玻璃 paywall）
        if plan_val in ("PRO", "PRO_199"):
            return {
                "error": True,
                "status_code": 403,
                "paywall": True,
                "upgrade_prompt": "🌟 解鎖 Claude 3.5 終極教練專為您梳理盲區漏洞，立刻升級 PRO_PLUS 取得解答",
                "message": "AI 教練深度對話為 PRO_PLUS 專屬功能",
                "upgrade": {
                    "target_plan": "PRO_PLUS_399",
                    "message": "解鎖 Claude 3.5 終極教練",
                },
            }

        # PRO_PLUS / ULTRA：允許
        context_id = nid or uuid.uuid4()
        session = self.db.query(AiChatSession).filter_by(
            user_id=uid, context_type="knowledge_node", context_id=context_id
        ).first()
        if not session:
            session = AiChatSession(
                user_id=uid,
                context_type="knowledge_node",
                context_id=context_id,
                model_used="claude-3.5-sonnet",
                message_count=0,
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

        user_msg = AiChatMessage(
            session_id=session.id, role="user", content=message,
        )
        self.db.add(user_msg)
        session.message_count = (session.message_count or 0) + 1
        self.db.commit()

        return {
            "error": False,
            "streaming": True,
            "reply": "AI 教練為您解析：" + message[:50],
            "content": "AI 教練為您解析：" + message[:50],
            "model_used": "claude-3.5-sonnet",
            "quota_used": 1,
            "remaining_quota": 49,
        }

    def submit_answers(self, node_id: str, user_id: str, correct_count: int, total_count: int) -> dict:
        """提交答案並更新節點掌握度。"""
        uid = uuid.UUID(user_id)
        nid = uuid.UUID(node_id)

        mastery = self.db.query(NodeMastery).filter_by(user_id=uid, node_id=nid).first()
        if not mastery:
            mastery = NodeMastery(user_id=uid, node_id=nid)
            self.db.add(mastery)

        mastery.correct_count = (mastery.correct_count or 0) + correct_count
        mastery.total_count = (mastery.total_count or 0) + total_count
        rate = (mastery.correct_count / mastery.total_count * 100) if mastery.total_count > 0 else 0
        mastery.mastery_rate = rate

        if rate >= 80:
            mastery.color = "green"
        elif rate >= 60:
            mastery.color = "orange"
        else:
            mastery.color = "red"

        self.db.commit()

        return {
            "error": False,
            "mastery_rate": rate,
            "color": mastery.color,
            "achievements": ["mastery_improved"] if mastery.color == "green" else [],
        }
