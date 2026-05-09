"""Knowledge Navigation service — business logic for 03b knowledge map navigation."""

import uuid

from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.learning_journey import LearningJourney
from app.models.resource import Resource
from app.models.resource_chunk import ResourceChunk
from app.models.resource_scaffold import ResourceScaffold
from app.models.subject import Subject
from app.models.ai_chat import AiChatSession, AiChatMessage
from app.models.user import User


class KnowledgeNavService:

    """Knowledge Nav Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db
        from app.services.prompt_template_service import PromptTemplateService
        self._prompt_svc = PromptTemplateService(db)
        self._llm = None

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """從 DB 載入 prompt 模板（render 變數），失敗回 None 由呼叫端 fallback hardcoded。"""
        import logging
        logger = logging.getLogger(__name__)
        try:
            result = self._prompt_svc.get_prompt_for_ai(name)
            if result.get("error"):
                return None
            if variables:
                render = self._prompt_svc.render_prompt
                result["system_prompt"] = render(result["system_prompt"], variables)
                result["user_prompt"] = render(result["user_prompt"], variables)
            return result
        except Exception as e:
            logger.warning("Failed to load prompt template '%s': %s", name, e)
            return None

    def _get_llm(self):
        """Lazy-load LLMService."""
        if self._llm is None:
            from app.services.llm_service import LLMService
            self._llm = LLMService(self.db)
        return self._llm

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

        # 只查詢此科目自己的知識節點，不混入父科目的節點
        # 注意：不在此處自動建 exam_bank Resource。使用者若刪除該 Resource，
        # 不應因重開知識地圖頁就被重建。考古題 Resource 建立僅在 onboarding 流程。
        subject_ids = [sid]

        # 讀取使用者的隱藏 Resource 清單（軟隱藏，DELETE 非擁有資源時寫入）
        from app.models.user_hidden_resource import UserHiddenResource
        hidden_resource_ids = {
            row[0] for row in
            self.db.query(UserHiddenResource.resource_id)
            .filter(UserHiddenResource.user_id == uid)
            .all()
        }

        # 找此科目下所有資源（排除使用者已隱藏的）
        resources_q = self.db.query(Resource).filter(Resource.subject_id.in_(subject_ids))
        if hidden_resource_ids:
            resources_q = resources_q.filter(~Resource.id.in_(hidden_resource_ids))
        resources = resources_q.all()
        resource_ids = [r.id for r in resources]

        # 只查統一知識樹節點（resource_id IS NULL）
        # per-resource 節點是文件處理的中間產物，不應出現在知識庫列表
        nodes_q = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.subject_id.in_(subject_ids),
            KnowledgeNode.resource_id.is_(None),
        )
        if hidden_resource_ids:
            # 保險：若未來開放 per-resource 節點顯示，此過濾仍生效
            nodes_q = nodes_q.filter(
                (KnowledgeNode.resource_id.is_(None))
                | (~KnowledgeNode.resource_id.in_(hidden_resource_ids))
            )
        nodes = nodes_q.order_by(KnowledgeNode.sort_order).all()

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
            """sort tree。"""
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

        # 判斷來源類型：優先看 resource；若節點無 resource（統一知識樹）則依溯源欄位推斷
        if resource:
            resource_type_val = resource.type.value if hasattr(resource.type, 'value') else resource.type
            is_youtube = resource_type_val == "youtube"
        else:
            is_youtube = bool(node.source_timestamp_seconds) and not node.source_page_number

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

    def get_node_scaffolds(self, node_id: str, user_id: str) -> dict:
        """取得節點對應的學習鷹架清單。

        Sprint 10 T85 重寫 — 走 scaffold_node_links N:M 表（embedding cosine）。
        舊的 page 比對 / chapter_heading 子字串對應已棄用（命中率太低）。
        FREE 用戶 403（TASK-04）。

        策略：
        - 直接從 scaffold_node_links 取該 node 的所有 link，按 similarity 降冪
        - 無命中時誠實回空陣列（教育原則：誤導 > 缺漏）
        - 前端應顯示「此節點尚無對應鷹架」，不再 fallback 到 resource 全集
        """
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return {"error": True, "status_code": 400, "message": "使用者 ID 格式錯誤"}
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        plan = user.subscription_plan
        plan_val = plan.value if hasattr(plan, "value") else plan
        if plan_val in (None, "FREE"):
            return {
                "error": True,
                "status_code": 403,
                "paywall": True,
                "message": "學習教材為 PRO 以上方案功能",
                "upgrade": {
                    "target_plan": "PRO_199",
                    "message": "升級 PRO 解鎖 AI 學習教材與延伸思考",
                },
            }

        try:
            nid = uuid.UUID(node_id)
        except ValueError:
            return {"error": True, "status_code": 400, "message": "節點 ID 格式錯誤"}

        node = self.db.query(KnowledgeNode).filter_by(id=nid).first()
        if not node:
            return {"error": True, "status_code": 404, "message": "知識節點不存在"}

        # Sprint 10 T85：走 scaffold_node_links N:M 表
        from sqlalchemy import text as sql_text
        rows = self.db.execute(sql_text(
            """
            SELECT s.id, s.type, s.chapter_heading, s.content,
                   s.page_start, s.page_end,
                   s.user_response, s.responded_at, s.reference_answer,
                   l.similarity
            FROM scaffold_node_links l
            JOIN resource_scaffolds s ON s.id = l.scaffold_id
            WHERE l.node_id = :nid
            ORDER BY l.similarity DESC
            LIMIT 20
            """
        ), {"nid": str(nid)}).fetchall()

        return {
            "error": False,
            "node_id": node_id,
            "scaffolds": [
                {
                    "id": str(r[0]),
                    "type": r[1].value if hasattr(r[1], "value") else r[1],
                    "chapter_heading": r[2],
                    "content": r[3],
                    "page_start": r[4],
                    "page_end": r[5],
                    "user_response": r[6],
                    "responded_at": r[7].isoformat() if r[7] else None,
                    "reference_answer": r[8],
                    "similarity": round(float(r[9]), 3),
                }
                for r in rows
            ],
        }

    def get_resource_scaffolds(self, resource_id: str, user_id: str) -> dict:
        """取得資源層級的學習鷹架（Spec 11 §「解析內容」入口）。

        用法：從學習庫「解析內容」連結進入知識地圖時，顯示該資源所有 scaffolds，
        不限定到單一 KnowledgeNode（避開「統一樹節點 resource_id IS NULL」架構限制）。

        FREE 用戶 403（與 get_node_scaffolds 一致）。
        """
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return {"error": True, "status_code": 400, "message": "使用者 ID 格式錯誤"}
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        plan = user.subscription_plan
        plan_val = plan.value if hasattr(plan, "value") else plan
        if plan_val in (None, "FREE"):
            return {
                "error": True,
                "status_code": 403,
                "paywall": True,
                "message": "學習教材為 PRO 以上方案功能",
                "upgrade": {
                    "target_plan": "PRO_199",
                    "message": "升級 PRO 解鎖 AI 學習教材與延伸思考",
                },
            }

        try:
            rid = uuid.UUID(resource_id)
        except ValueError:
            return {"error": True, "status_code": 400, "message": "資源 ID 格式錯誤"}

        resource = self.db.query(Resource).filter_by(id=rid).first()
        if not resource:
            return {"error": True, "status_code": 404, "message": "資源不存在"}
        if resource.user_id != uid:
            return {"error": True, "status_code": 403, "message": "無存取此資源的權限"}

        scaffolds = (
            self.db.query(ResourceScaffold)
            .filter(ResourceScaffold.resource_id == rid)
            .order_by(ResourceScaffold.page_start.nulls_last(), ResourceScaffold.created_at)
            .all()
        )
        return {
            "error": False,
            "resource_id": resource_id,
            "scaffolds": [
                {
                    "id": str(s.id),
                    "type": s.type.value if hasattr(s.type, "value") else s.type,
                    "chapter_heading": s.chapter_heading,
                    "content": s.content,
                    "page_start": s.page_start,
                    "page_end": s.page_end,
                    "user_response": s.user_response,
                    "responded_at": s.responded_at.isoformat() if s.responded_at else None,
                }
                for s in scaffolds
            ],
        }

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
                "upgrade_prompt": "🌟 解鎖 Gemini AI 終極教練專為您梳理盲區漏洞，立刻升級 PRO_PLUS 取得解答",
                "message": "AI 教練深度對話為 PRO_PLUS 專屬功能",
                "upgrade": {
                    "target_plan": "PRO_PLUS_399",
                    "message": "解鎖 Gemini AI 終極教練",
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
                model_used="gemini-2.5-flash",
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

        # ── 真正呼叫 LLM 產生回覆（T-02 coach_advanced 模板，fallback hardcoded） ──
        reply_text = self._generate_coach_reply(nid, message, plan_val)

        # 存 assistant 訊息
        assistant_msg = AiChatMessage(
            session_id=session.id, role="assistant", content=reply_text,
        )
        self.db.add(assistant_msg)
        session.message_count = (session.message_count or 0) + 1
        self.db.commit()

        from datetime import datetime, timezone
        return {
            "error": False,
            "streaming": True,
            # 三種欄位都帶，相容前端各種讀取方式
            "message": reply_text,                # frontend knowledge/page.tsx 讀此欄
            "content": reply_text,
            "reply": {                            # frontend review/page.tsx 期待的 ChatMessage shape
                "id": f"msg_ai_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "role": "ai",
                "content": reply_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "model_used": "gemini-2.5-flash",
            "quota_used": 1,
            "remaining_quota": 49,
        }

    def _generate_coach_reply(self, node_id: uuid.UUID | None, message: str, plan_val: str) -> str:
        """產生 AI 教練回覆。優先用 T-02 coach_advanced 模板 + RAG 上下文，
        模板異常或 LLM 不可用時 fallback 到內建蘇格拉底教練人格。"""
        import logging
        logger = logging.getLogger(__name__)

        # 1. 收集節點上下文
        subject_name = "備考科目"
        node_name = "此概念"
        mastery_rate = "0"
        source_content = ""
        if node_id:
            node = self.db.query(KnowledgeNode).filter_by(id=node_id).first()
            if node:
                node_name = node.name or "此概念"
                subj = self.db.query(Subject).filter_by(id=node.subject_id).first()
                if subj:
                    subject_name = subj.name
                # 取掌握度（無 user_id 跳過）
                # mastery_rate 留空字串避免 prompt 出現 "0%" 誤導
                # RAG：抓節點所在資源最多 3 chunks 當溯源內容
                if node.resource_id:
                    chunks = self.db.query(ResourceChunk).filter_by(
                        resource_id=node.resource_id
                    ).limit(3).all()
                    if chunks:
                        source_content = "\n\n".join(
                            f"## {c.section_title or '段落'}\n{c.content[:500]}"
                            for c in chunks
                        )

        # 2. 嘗試 DB 模板
        db_prompt = self._load_prompt("coach_advanced", {
            "subject_name": subject_name,
            "node_name": node_name,
            "mastery_rate": mastery_rate,
            "user_background_instruction": "",
            "source_content": source_content or "（無溯源內容）",
            "user_input": message,
        })

        # 3. fallback hardcoded prompt
        if db_prompt and db_prompt.get("system_prompt") and db_prompt.get("user_prompt"):
            system_prompt = db_prompt["system_prompt"]
            user_prompt = db_prompt["user_prompt"]
        else:
            system_prompt = (
                f"你是 TiTi 平台 AI 教練 Certi，正在協助學習「{subject_name}」中的「{node_name}」。\n"
                "用蘇格拉底式提問引導學生思考；不直接給答案，而是用 1-2 個引導問題。\n"
                "語氣溫暖、簡潔（200 字內），可引用教材內容。"
            )
            user_prompt = (
                f"知識節點：{node_name}\n"
                f"科目：{subject_name}\n\n"
                f"教材參考：\n{source_content or '（無）'}\n\n"
                f"學生提問：{message}"
            )

        # 4. 呼叫 LLM
        try:
            llm = self._get_llm()
            reply = llm.generate(
                system_prompt, user_prompt,
                plan=plan_val if plan_val in ("PRO_PLUS", "ULTRA") else "PRO_PLUS",
                task_type="advanced", max_tokens=1024,
                feature="ai_coach_chat",
            )
            return reply.strip() if reply else "抱歉，目前無法產生回覆，請稍後再試。"
        except Exception as e:
            logger.warning("knowledge_nav coach LLM call failed: %s", e)
            return "抱歉，AI 教練暫時無法回覆。請稍後再試。"

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
