"""Knowledge Merge Service — 知識樹合併對齊業務邏輯。

🔧 後台自動觸發功能（2026-04-28 起）：
此服務已轉為**後台自動觸發**，前端 UI 已移除。觸發點：
  - DocumentProcessingService Step 11（每次資源上傳完成後）自動呼叫 .merge()
  - similarity >= 0.85 自動 merge / 0.65-0.85 落 MergeConflict / < 0.65 add as new
  - 失敗只 log warning 不阻斷上傳

admin endpoints (`/api/v1/knowledge-merge/*`) 保留作為 monitoring / override：
  - 列衝突 / 解決衝突 / 看 merge 歷史
這些 endpoint 仍可用，但前端不再提供操作頁；如需呼叫請直接打 API 或寫 admin 工具。
"""

import difflib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode
from app.models.merge_conflict import MergeConflict
from app.models.merge_history import MergeHistory
from app.models.user import User

logger = logging.getLogger(__name__)

# Similarity thresholds
THRESHOLD_AUTO_MERGE = 0.75
THRESHOLD_CONFLICT = 0.55

# LLM 語意比對的 fallback prompt
_FALLBACK_MERGE_SYSTEM_PROMPT = """你是知識圖譜對齊專家。比對以下兩個知識節點的語意相似度。

判斷規則：
- similarity >= 0.85：建議自動合併（名稱不同但概念相同）
- 0.65 <= similarity < 0.85：標記衝突，建議人工審核
- similarity < 0.65：保持獨立（不同概念）

考慮因素：
1. 節點名稱的語意（非字面）相似度
2. 節點描述的內容重疊程度
3. 節點所在層級是否對等
4. 考綱來源（syllabus）的名稱優先於個人筆記（personal）

僅回覆 JSON：
{
  "similarity": 0.92,
  "suggestion": "merge|review|keep_separate",
  "reason": "兩者皆指 AWS EC2 虛擬伺服器，僅名稱差異",
  "preferred_name": "EC2 運算服務"
}"""


class KnowledgeMergeService:

    """Knowledge Merge Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db
        self._prompt_svc = None

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """嘗試從 DB 載入 prompt 模板，失敗回傳 None。"""
        try:
            if self._prompt_svc is None:
                from app.services.prompt_template_service import PromptTemplateService
                self._prompt_svc = PromptTemplateService(self.db)
            result = self._prompt_svc.get_prompt_for_ai(name, variables or {})
            if not result.get("error"):
                return result
        except Exception:
            pass
        return None

    def _get_llm_service(self):
        """取得 LLMService 實例（lazy init）。"""
        try:
            from app.services.llm_service import LLMService
            return LLMService()
        except Exception:
            return None

    def _llm_compare_nodes(
        self,
        existing_node: KnowledgeNode,
        incoming: dict,
    ) -> dict | None:
        """用 LLM 做語意比對，回傳 {similarity, suggestion, reason, preferred_name} 或 None。"""
        llm = self._get_llm_service()
        if not llm:
            return None

        existing_origin = existing_node.source_origin or "document"
        incoming_origin = incoming.get("source_origin", "document")

        node_a_json = json.dumps({
            "name": existing_node.name,
            "description": existing_node.source_text or "",
        }, ensure_ascii=False)
        node_b_json = json.dumps({
            "name": incoming.get("name", ""),
            "description": incoming.get("description", ""),
        }, ensure_ascii=False)

        # 嘗試從 DB 載入 prompt
        db_prompt = self._load_prompt("knowledge_tree_merge", {
            "node_type_a": existing_origin,
            "node_a": node_a_json,
            "node_type_b": incoming_origin,
            "node_b": node_b_json,
        })

        if db_prompt:
            system_prompt = db_prompt["system_prompt"]
            user_prompt = db_prompt["user_prompt"]
        else:
            system_prompt = _FALLBACK_MERGE_SYSTEM_PROMPT
            user_prompt = f"節點 A（{existing_origin}）：{node_a_json}\n節點 B（{incoming_origin}）：{node_b_json}"

        try:
            raw = llm.generate(
                system_prompt,
                user_prompt,
                model="gemini-flash",
                max_tokens=256,
                feature="knowledge_merge",
            )
            return self._parse_llm_response(raw)
        except Exception as e:
            logger.warning("LLM merge comparison failed: %s", e)
            return None

    @staticmethod
    def _parse_llm_response(raw) -> dict | None:
        """解析 LLM 回傳的 JSON。"""
        if not raw:
            return None
        text = raw if isinstance(raw, str) else str(raw)
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return None

    # ========== Helpers ==========

    def _get_user(self, user_id: str) -> Optional[User]:
        """取得 user。"""
        return self.db.query(User).filter_by(id=uuid.UUID(user_id)).first()

    def _validate_user(self, user_id: str) -> dict | None:
        """驗證 user。"""
        user = self._get_user(user_id)
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}
        return None

    # ========== Compare ==========

    @staticmethod
    def compare_nodes(existing_name: str, incoming_name: str) -> float:
        """Return similarity score between two node names.

        Uses SequenceMatcher as base, with a bonus for substring containment.
        """
        a = existing_name.lower().strip()
        b = incoming_name.lower().strip()
        base_score = difflib.SequenceMatcher(None, a, b).ratio()

        # Boost score if one name contains the other (strong semantic signal)
        if a in b or b in a:
            base_score = max(base_score, 0.70)

        return base_score

    # ========== Merge Pipeline ==========

    def merge(
        self,
        user_id: str,
        subject_id: str,
        incoming_nodes: list[dict],
        trigger_source: str = "document",
        trigger_name: str = "",
    ) -> dict:
        """Main merge pipeline.

        For each incoming node:
        - similarity >= 0.85: auto-merge (keep existing name, append source_origin)
        - 0.65 <= similarity < 0.85: create MergeConflict for manual review
        - similarity < 0.65: add as new node
        """
        err = self._validate_user(user_id)
        if err:
            return err

        sid = uuid.UUID(subject_id)

        original_existing = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.subject_id == sid)
            .all()
        )

        nodes_added = 0
        nodes_merged = 0
        conflicts_count = 0
        added_nodes = []
        merged_nodes = []
        conflict_records = []
        # Track newly added node names to avoid comparing incoming nodes
        # against each other (only compare against original existing nodes)
        newly_added: list[KnowledgeNode] = []

        for incoming in incoming_nodes:
            incoming_name = incoming.get("name", "").strip()
            if not incoming_name:
                continue

            incoming_source = incoming.get("source_origin", "document")
            incoming_parent_id = incoming.get("parent_id")
            incoming_depth = incoming.get("depth", 0)
            incoming_sort_order = incoming.get("sort_order", 0)

            # Find best match among ORIGINAL existing nodes only
            best_match: Optional[KnowledgeNode] = None
            best_score = 0.0

            for node in original_existing:
                score = self.compare_nodes(node.name, incoming_name)
                # Prefer substring matches when scores are equal
                is_substring = (
                    node.name in incoming_name or incoming_name in node.name
                )
                current_is_substring = (
                    best_match is not None
                    and (best_match.name in incoming_name or incoming_name in best_match.name)
                ) if best_match else False

                if score > best_score or (
                    score == best_score and is_substring and not current_is_substring
                ):
                    best_score = score
                    best_match = node

            if best_score >= THRESHOLD_AUTO_MERGE and best_match is not None:
                # Auto-merge: keep existing name, update source_origin
                origins = set(
                    (best_match.source_origin or "").split(",")
                )
                origins.discard("")
                origins.add(incoming_source)
                best_match.source_origin = ",".join(sorted(origins))
                nodes_merged += 1
                merged_nodes.append({
                    "existing_node_id": str(best_match.id),
                    "existing_name": best_match.name,
                    "incoming_name": incoming_name,
                    "similarity": round(best_score, 4),
                })

            elif best_score >= THRESHOLD_CONFLICT and best_match is not None:
                # Gray zone: 先嘗試 LLM 語意比對做更精確判斷
                llm_result = self._llm_compare_nodes(best_match, incoming)

                if llm_result and "similarity" in llm_result:
                    llm_sim = float(llm_result["similarity"])
                    llm_suggestion = llm_result.get("suggestion", "review")
                    preferred_name = llm_result.get("preferred_name")

                    if llm_sim >= 0.85 or llm_suggestion == "merge":
                        # LLM 判定應合併
                        origins = set(
                            (best_match.source_origin or "").split(",")
                        )
                        origins.discard("")
                        origins.add(incoming_source)
                        best_match.source_origin = ",".join(sorted(origins))
                        # 若 LLM 建議了 preferred_name，更新節點名稱
                        if preferred_name and preferred_name != best_match.name:
                            best_match.name = preferred_name
                        nodes_merged += 1
                        merged_nodes.append({
                            "existing_node_id": str(best_match.id),
                            "existing_name": best_match.name,
                            "incoming_name": incoming_name,
                            "similarity": round(llm_sim, 4),
                            "llm_enhanced": True,
                            "reason": llm_result.get("reason", ""),
                        })
                        continue

                    elif llm_sim < 0.65 or llm_suggestion == "keep_separate":
                        # LLM 判定不相關 → 新增為獨立節點
                        parent_uuid = (
                            uuid.UUID(incoming_parent_id)
                            if incoming_parent_id
                            else None
                        )
                        new_node = KnowledgeNode(
                            subject_id=sid,
                            parent_id=parent_uuid,
                            name=incoming_name,
                            depth=incoming_depth,
                            sort_order=incoming_sort_order,
                            source_origin=incoming_source,
                        )
                        self.db.add(new_node)
                        newly_added.append(new_node)
                        nodes_added += 1
                        added_nodes.append({
                            "name": incoming_name,
                            "source_origin": incoming_source,
                            "llm_enhanced": True,
                        })
                        continue

                    # LLM 也不確定 → 仍然建立 conflict，但用 LLM 的 similarity
                    best_score = llm_sim

                # Fallback: 建立衝突待人工審核
                suggestion = self._suggest_resolution(best_score, best_match, incoming)
                conflict = MergeConflict(
                    subject_id=sid,
                    existing_node_id=best_match.id,
                    incoming_node_name=incoming_name,
                    similarity=Decimal(str(round(best_score, 2))),
                    status="pending_review",
                    suggestion=suggestion,
                )
                self.db.add(conflict)
                conflicts_count += 1
                conflict_records.append({
                    "existing_name": best_match.name,
                    "incoming_name": incoming_name,
                    "similarity": round(best_score, 4),
                    "suggestion": suggestion,
                })

            else:
                # New node
                parent_uuid = (
                    uuid.UUID(incoming_parent_id)
                    if incoming_parent_id
                    else None
                )
                new_node = KnowledgeNode(
                    subject_id=sid,
                    parent_id=parent_uuid,
                    name=incoming_name,
                    depth=incoming_depth,
                    sort_order=incoming_sort_order,
                    source_origin=incoming_source,
                )
                self.db.add(new_node)
                newly_added.append(new_node)
                nodes_added += 1
                added_nodes.append({
                    "name": incoming_name,
                    "source_origin": incoming_source,
                })

        # Record merge history
        history = MergeHistory(
            subject_id=sid,
            trigger_source=trigger_source,
            trigger_name=trigger_name or f"merge_{len(incoming_nodes)}_nodes",
            nodes_added=nodes_added,
            nodes_merged=nodes_merged,
            conflicts_count=conflicts_count,
        )
        self.db.add(history)
        self.db.commit()

        return {
            "nodes_added": nodes_added,
            "nodes_merged": nodes_merged,
            "conflicts_count": conflicts_count,
            "added": added_nodes,
            "merged": merged_nodes,
            "conflicts": conflict_records,
        }

    @staticmethod
    def _suggest_resolution(
        score: float,
        existing: KnowledgeNode,
        incoming: dict,
    ) -> str:
        """Suggest a resolution based on similarity and source."""
        if score >= 0.80:
            return "merge"
        existing_origin = existing.source_origin or ""
        if "exam" in existing_origin:
            return "merge_as_child"
        return "keep_separate"

    # ========== Conflicts ==========

    def get_conflicts(self, user_id: str, subject_id: str) -> dict:
        """取得 conflicts。"""
        err = self._validate_user(user_id)
        if err:
            return err

        sid = uuid.UUID(subject_id)
        conflicts = (
            self.db.query(MergeConflict)
            .filter(
                MergeConflict.subject_id == sid,
                MergeConflict.status == "pending_review",
            )
            .order_by(MergeConflict.created_at.desc())
            .all()
        )

        items = []
        for c in conflicts:
            existing_node = None
            if c.existing_node_id:
                existing_node = (
                    self.db.query(KnowledgeNode)
                    .filter_by(id=c.existing_node_id)
                    .first()
                )
            items.append({
                "id": str(c.id),
                "existing_node_id": str(c.existing_node_id) if c.existing_node_id else None,
                "existing_node_name": existing_node.name if existing_node else None,
                "incoming_node_name": c.incoming_node_name,
                "similarity": float(c.similarity),
                "suggestion": c.suggestion,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })

        return {"conflicts": items}

    def resolve_conflict(self, user_id: str, conflict_id: str, action: str) -> dict:
        """Resolve a conflict with the given action (merge/merge_as_child/keep_separate)."""
        err = self._validate_user(user_id)
        if err:
            return err

        valid_actions = {"merge", "merge_as_child", "keep_separate"}
        if action not in valid_actions:
            return {
                "error": True,
                "status_code": 400,
                "message": f"無效的解決方式，允許的值: {', '.join(sorted(valid_actions))}",
            }

        conflict = (
            self.db.query(MergeConflict)
            .filter_by(id=uuid.UUID(conflict_id))
            .first()
        )
        if not conflict:
            return {"error": True, "status_code": 404, "message": "衝突記錄不存在"}

        if conflict.status == "resolved":
            return {"error": True, "status_code": 400, "message": "此衝突已解決"}

        uid = uuid.UUID(user_id)

        if action == "merge" and conflict.existing_node_id:
            existing_node = (
                self.db.query(KnowledgeNode)
                .filter_by(id=conflict.existing_node_id)
                .first()
            )
            if existing_node:
                origins = set((existing_node.source_origin or "").split(","))
                origins.discard("")
                origins.add("document")
                existing_node.source_origin = ",".join(sorted(origins))

        elif action == "merge_as_child" and conflict.existing_node_id:
            # Create incoming as child of existing node
            new_node = KnowledgeNode(
                subject_id=conflict.subject_id,
                parent_id=conflict.existing_node_id,
                name=conflict.incoming_node_name,
                depth=1,  # relative child
                sort_order=0,
                source_origin="document",
            )
            self.db.add(new_node)

        elif action == "keep_separate":
            # Create incoming as standalone node — depth=1 per migration 091
            # chk_depth_range CHECK (1..3); standalone roots act as top-level chapters.
            new_node = KnowledgeNode(
                subject_id=conflict.subject_id,
                parent_id=None,
                name=conflict.incoming_node_name,
                depth=1,
                sort_order=0,
                source_origin="document",
            )
            self.db.add(new_node)

        conflict.status = "resolved"
        conflict.resolution = action
        conflict.resolved_by = uid
        conflict.resolved_at = datetime.now(timezone.utc)

        self.db.commit()

        return {
            "conflict_id": str(conflict.id),
            "resolution": action,
            "status": "resolved",
        }

    # ========== History ==========

    def get_history(self, user_id: str, subject_id: str) -> dict:
        """取得 history。"""
        err = self._validate_user(user_id)
        if err:
            return err

        sid = uuid.UUID(subject_id)
        records = (
            self.db.query(MergeHistory)
            .filter(MergeHistory.subject_id == sid)
            .order_by(MergeHistory.merged_at.desc())
            .all()
        )

        items = []
        for r in records:
            items.append({
                "id": str(r.id),
                "trigger_source": r.trigger_source,
                "trigger_name": r.trigger_name,
                "nodes_added": r.nodes_added,
                "nodes_merged": r.nodes_merged,
                "conflicts_count": r.conflicts_count,
                "merged_at": r.merged_at.isoformat() if r.merged_at else None,
            })

        return {"history": items}

    # ========== Node Detail ==========

    def get_node_detail(self, user_id: str, node_id: str) -> dict:
        """Get node with metadata including source_origins and aliases."""
        err = self._validate_user(user_id)
        if err:
            return err

        node = (
            self.db.query(KnowledgeNode)
            .filter_by(id=uuid.UUID(node_id))
            .first()
        )
        if not node:
            return {"error": True, "status_code": 404, "message": "知識節點不存在"}

        origins = [o for o in (node.source_origin or "").split(",") if o]

        children = (
            self.db.query(KnowledgeNode)
            .filter_by(parent_id=node.id)
            .order_by(KnowledgeNode.sort_order)
            .all()
        )

        # Check for pending conflicts related to this node
        pending_conflicts = (
            self.db.query(MergeConflict)
            .filter(
                MergeConflict.existing_node_id == node.id,
                MergeConflict.status == "pending_review",
            )
            .all()
        )

        # Derive aliases from resolved merge conflicts (incoming names)
        resolved_conflicts = (
            self.db.query(MergeConflict)
            .filter(
                MergeConflict.existing_node_id == node.id,
                MergeConflict.status == "resolved",
                MergeConflict.resolution == "merge",
            )
            .all()
        )
        aliases = [rc.incoming_node_name for rc in resolved_conflicts]

        # Derive mapped_question_count from questions linked to this node
        from app.models.question import Question
        mapped_question_count = (
            self.db.query(Question)
            .filter(Question.node_id == node.id)
            .count()
        )

        # Last merged_at from merge history
        last_history = (
            self.db.query(MergeHistory)
            .filter(MergeHistory.subject_id == node.subject_id)
            .order_by(MergeHistory.merged_at.desc())
            .first()
        )
        last_merged_at = (
            last_history.merged_at.isoformat()
            if last_history and last_history.merged_at
            else None
        )

        # Document refs from source_text
        document_refs = []
        if node.source_text:
            document_refs.append(node.source_text)

        return {
            "id": str(node.id),
            "subject_id": str(node.subject_id) if node.subject_id else None,
            "parent_id": str(node.parent_id) if node.parent_id else None,
            "name": node.name,
            "depth": node.depth,
            "sort_order": node.sort_order,
            "source_origins": origins,
            "aliases": aliases,
            "mapped_question_count": mapped_question_count,
            "document_refs": document_refs,
            "exam_frequency": node.exam_frequency,
            "available_questions": node.available_questions,
            "last_merged_at": last_merged_at,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "children": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "depth": c.depth,
                    "source_origin": c.source_origin,
                }
                for c in children
            ],
            "pending_conflicts": [
                {
                    "id": str(pc.id),
                    "incoming_node_name": pc.incoming_node_name,
                    "similarity": float(pc.similarity),
                    "suggestion": pc.suggestion,
                }
                for pc in pending_conflicts
            ],
        }
