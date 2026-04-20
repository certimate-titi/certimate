"""Knowledge Navigation service — business logic for 03b knowledge map navigation."""

import uuid

from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.learning_journey import LearningJourney
from app.models.resource import Resource
from app.models.resource_chunk import ResourceChunk
from app.models.subject import Subject
from app.models.ai_chat import AiChatSession, AiChatMessage
from app.models.user import User


class KnowledgeNavService:

    def __init__(self, db: Session):
        self.db = db

    def _ensure_exam_bank_resource(self, subject_id: uuid.UUID) -> None:
        """若科目有考古題但無 Resource，觸發自動建立。

        若子科目本身無考古題，會自動查找同名父科目的考古題。
        例如「AI 應用規劃師（初級）」→「AI 應用規劃師」。
        """
        from app.models.subject import Subject
        from app.services.onboarding_service import OnboardingService

        subject = self.db.query(Subject).filter_by(id=subject_id).first()
        if not subject:
            return

        # 已有 Resource → 跳過
        existing = self.db.query(Resource).filter_by(subject_id=subject_id).first()
        if existing:
            return

        # 若本科目有題 → 直接建立
        if subject.available_questions and subject.available_questions > 0:
            svc = OnboardingService(self.db)
            svc._ensure_exam_bank_resource(subject)
            self.db.flush()
            return

        # 子科目無題 → 優先透過 parent_subject_id FK 查找父科目
        if subject.parent_subject_id:
            parent = self.db.query(Subject).filter_by(id=subject.parent_subject_id).first()
            if parent and parent.available_questions and parent.available_questions > 0:
                subject.available_questions = parent.available_questions
                self.db.flush()
                svc = OnboardingService(self.db)
                svc._ensure_exam_bank_resource(subject, parent_subject=parent)
                self.db.flush()
                return

        # TODO(deprecate): 字串比對 fallback — 待所有 subjects 都設定 parent_subject_id 後移除
        base_name = subject.name.split("（")[0].strip()
        if base_name != subject.name:
            parent = (
                self.db.query(Subject)
                .filter(Subject.name == base_name)
                .filter(Subject.available_questions > 0)
                .first()
            )
            if parent:
                # 繼承父科目的題數
                subject.available_questions = parent.available_questions
                self.db.flush()
                svc = OnboardingService(self.db)
                svc._ensure_exam_bank_resource(subject, parent_subject=parent)
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

        # 確保考古題 Resource 存在（並 commit 以持久化）
        # Defensive: 任何錯誤都不該讓整個 endpoint 回 500 — 使用者至少該看到
        # 已存在的 knowledge_nodes，即使 synthetic resource 創建失敗。
        try:
            self._ensure_exam_bank_resource(sid)
            self.db.commit()
        except Exception as exc:
            import logging
            logging.getLogger("knowledge_nav").warning(
                "[ensure_exam_bank] failed for subject %s: %s", sid, exc,
            )
            try:
                self.db.rollback()
            except Exception:
                pass

        # 只查詢此科目自己的知識節點，不混入父科目的節點
        subject_ids = [sid]

        # 找此科目下所有資源
        resources = self.db.query(Resource).filter(Resource.subject_id.in_(subject_ids)).all()
        resource_ids = [r.id for r in resources]

        # 只查統一知識樹節點（resource_id IS NULL）
        # per-resource 節點是文件處理的中間產物，不應出現在知識庫列表
        nodes = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.subject_id.in_(subject_ids),
            KnowledgeNode.resource_id.is_(None),
        ).order_by(KnowledgeNode.sort_order).all()

        # 找掌握度
        node_ids = [n.id for n in nodes]
        masteries = self.db.query(NodeMastery).filter(
            NodeMastery.user_id == uid,
            NodeMastery.node_id.in_(node_ids)
        ).all()
        mastery_map = {str(m.node_id): m for m in masteries}

        # Build flat node list — SM-2 記憶衰退計算
        from app.services.sm2_engine import SM2Engine, TopicState
        sm2 = SM2Engine()
        flat_nodes = {}

        for node in nodes:
            m = mastery_map.get(str(node.id))

            if m and m.base_mastery and m.base_mastery > 0:
                # 有 SM-2 資料 → 計算 effective_progress（含記憶衰退）
                state = TopicState(
                    base_mastery=m.base_mastery,
                    ease_factor=m.ease_factor or SM2Engine.DEFAULT_EASE_FACTOR,
                    last_tested_at=m.last_tested_at,
                    next_review_at=m.next_review_at,
                    status=m.status or "UNSEEN",
                )
                effective = sm2.calculate_effective_progress(state)
                decay_status = sm2.get_decay_status(state)
                display_color = (
                    "green" if effective >= 0.7 else
                    "yellow" if effective >= 0.4 else
                    "red" if effective > 0 else "gray"
                )
                progress = effective
                status = (
                    "MASTERED" if effective >= 0.7 else
                    "PENDING" if effective >= 0.4 else
                    "CRITICAL" if effective > 0 else "UNSEEN"
                )
            elif m:
                progress = float(m.mastery_rate or 0) / 100.0
                display_color = m.color if m.color else (
                    "green" if progress >= 0.7 else
                    "yellow" if progress >= 0.4 else
                    "red" if progress > 0 else "gray"
                )
                status = m.status if m.status else "UNSEEN"
                decay_status = "fresh"
            else:
                progress = 0.0
                display_color = "gray"
                status = "UNSEEN"
                decay_status = "unseen"

            # Mindmap upgrade §3 — support_strength display hints
            from app.services.mindmap_strength_service import MindmapStrengthService
            strength_value = getattr(node, "support_strength", 1.0) or 0.0
            strength_hint = MindmapStrengthService.strength_to_display(strength_value)

            # Empty/sparse nodes override decay color with gray "待補充"
            if strength_hint["needs_supplement"]:
                display_color = strength_hint["color"]

            flat_nodes[str(node.id)] = {
                "id": str(node.id),
                "name": node.name,
                "depth": node.depth,
                "parent_id": str(node.parent_id) if node.parent_id else None,
                "resource_id": str(node.resource_id) if node.resource_id else None,
                "sort_order": node.sort_order or 0,
                "source_page": node.source_page_number,
                "available_questions": node.available_questions or 0,
                "mastery_rate": int(progress * 100),
                "mastery_color": display_color,
                "status": status,
                "decay_status": decay_status,
                "progress_percentage": round(progress, 4),
                # §3 新增
                "support_strength": round(float(strength_value), 3),
                "strength_tier": strength_hint["tier"],
                "strength_label": strength_hint["label"],
                "needs_supplement": strength_hint["needs_supplement"],
                "node_source": getattr(node, "node_source", "user_data"),
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
            {
                "id": str(r.id),
                "name": r.name,
                "type": r.type.value if hasattr(r.type, 'value') else r.type,
                "status": r.status.value if hasattr(r.status, 'value') else (r.status or "pending"),
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in resources
        ]

        # 合併預載考古題（嚴守科目隔離 — 僅用該 subject 自己的 exam_subject_codes）
        try:
            from app.services.historical_markdown_service import HistoricalMarkdownService
            for h in HistoricalMarkdownService(self.db).list_for_subject(subject_id):
                result_resources.append({
                    "id": f"hist:{h['id']}",
                    "name": h["name"],
                    "type": "historical_exam",
                    "status": "completed",
                    "error_message": None,
                    "created_at": None,
                    "historical_exam_id": h["id"],
                    "total_questions": h["total_questions"],
                    "year": h["year"],
                })
        except Exception:
            pass

        # PRD-034 US-02: 合法空態區分
        empty_reason = None
        if not roots:
            if not result_resources:
                empty_reason = "no_resources"
            else:
                empty_reason = "no_nodes_generated"

        return {
            "error": False,
            "nodes": roots,
            "resources": result_resources,
            "empty_reason": empty_reason,
        }

    def get_node_detail(self, node_id: str, user_id: str) -> dict:
        """取得節點詳情（含溯源資訊）。"""
        node = self.db.query(KnowledgeNode).filter_by(
            id=uuid.UUID(node_id)
        ).first()
        if not node:
            return {"error": True, "status_code": 404, "message": "知識節點不存在"}

        resource = self.db.query(Resource).filter_by(id=node.resource_id).first() if node.resource_id else None

        # 判斷來源類型
        if resource:
            resource_type_val = resource.type.value if hasattr(resource.type, 'value') else resource.type
            is_youtube = resource_type_val == "youtube"
        else:
            is_youtube = False

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
        """取得節點溯源內容（含物理級跳轉資訊）。"""
        result = self.get_node_detail(node_id, user_id)
        if result.get("error"):
            return result

        # 查詢關聯的 chunk，取得物理級跳轉資訊
        nid = uuid.UUID(node_id)
        chunk = (
            self.db.query(ResourceChunk)
            .filter_by(node_id=nid, is_deleted=False)
            .order_by(ResourceChunk.chunk_index)
            .first()
        )

        if chunk:
            result["highlight"] = {
                "anchor_id": chunk.anchor_id,
                "line_start": chunk.highlight_line_start,
                "line_end": chunk.highlight_line_end,
                "char_start": chunk.highlight_char_start,
                "char_end": chunk.highlight_char_end,
                "page_start": chunk.source_page_start,
                "page_end": chunk.source_page_end,
            }
        else:
            result["highlight"] = None

        return result

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
            mastery.color = "yellow"
        else:
            mastery.color = "red"

        self.db.commit()

        return {
            "error": False,
            "mastery_rate": rate,
            "color": mastery.color,
            "achievements": ["mastery_improved"] if mastery.color == "green" else [],
        }
