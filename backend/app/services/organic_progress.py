"""V3+SM2 混合進度引擎 — 有機生長 + SM-2 記憶衰退.

核心邏輯：
- 練習/考試答題 → 即時更新 progress + SM-2 參數（base_mastery, ease_factor, next_review_at）
- 向上傳播（Upward Propagation）→ 父節點 = Σ(子.progress × 子.weight) / Σ(子.weight)
- 進度稀釋（Dilution）→ 考綱新增節點時，分母變大，進度自然下降
- 記憶衰退 → 超過 next_review_at 後，有效進度 = base_mastery × retention（指數衰退）
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.node_mastery import NodeMastery
from app.models.knowledge_node import KnowledgeNode
from app.services.sm2_engine import SM2Engine, TopicState

logger = logging.getLogger(__name__)

_sm2 = SM2Engine()


class OrganicProgressEngine:
    """V3 有機生長進度引擎。"""

    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    # ── 單題答案更新 ────────────────────────────────────────────

    def update_on_answer(
        self,
        user_id: str,
        node_id: str,
        is_correct: bool,
        weight: float = 1.0,
    ) -> dict:
        """答題後即時更新節點 progress + SM-2 記憶參數。

        同時更新：
        1. mastery_rate（EMA 即時進度，用於向上傳播）
        2. SM-2 欄位（base_mastery, ease_factor, next_review_at — 用於記憶衰退）

        Returns:
            {"node_id", "old_progress", "new_progress", "status"}
        """
        uid = uuid.UUID(user_id)
        nid = uuid.UUID(node_id)
        alpha = 0.2 * weight

        mastery = self.db.query(NodeMastery).filter(
            NodeMastery.user_id == uid, NodeMastery.node_id == nid
        ).first()

        if not mastery:
            mastery = NodeMastery(
                id=uuid.uuid4(), user_id=uid, node_id=nid,
                mastery_rate=0, correct_count=0, total_count=0,
            )
            self.db.add(mastery)
            self.db.flush()

        old_progress = float(mastery.mastery_rate or 0) / 100.0
        answer_score = 1.0 if is_correct else 0.0
        new_progress = old_progress * (1 - alpha) + answer_score * alpha
        new_progress = round(min(1.0, max(0.0, new_progress)), 4)

        # 更新 EMA 進度
        mastery.mastery_rate = round(new_progress * 100, 2)
        mastery.correct_count = (mastery.correct_count or 0) + (1 if is_correct else 0)
        mastery.total_count = (mastery.total_count or 0) + 1

        # 更新 SM-2 記憶參數
        current_state = TopicState(
            base_mastery=mastery.base_mastery or 0.0,
            ease_factor=mastery.ease_factor or SM2Engine.DEFAULT_EASE_FACTOR,
            last_tested_at=mastery.last_tested_at,
            next_review_at=mastery.next_review_at,
            status=mastery.status or "UNSEEN",
        )
        new_state = _sm2.process_answer(current_state, is_correct)
        mastery.base_mastery = new_state.base_mastery
        mastery.ease_factor = new_state.ease_factor
        mastery.last_tested_at = new_state.last_tested_at
        mastery.next_review_at = new_state.next_review_at

        # 狀態和顏色用 SM-2 的 base_mastery 決定
        mastery.color = self._progress_to_color(new_state.base_mastery)
        mastery.status = new_state.status

        return {
            "node_id": node_id,
            "old_progress": old_progress,
            "new_progress": new_progress,
            "status": mastery.status,
        }

    # ── 向上傳播（Upward Propagation）──────────────────────────

    def propagate_upward(self, user_id: str, leaf_node_id: str) -> list[dict]:
        """從葉節點向上重算所有祖先的 progress。

        Returns:
            [{"node_id", "new_progress", "child_count"}, ...]
        """
        uid = uuid.UUID(user_id)
        updated = []

        # 找到葉節點的 parent 鏈
        current_node = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.id == uuid.UUID(leaf_node_id)
        ).first()

        if not current_node or not current_node.parent_id:
            return updated

        # 逐層向上
        parent_id = current_node.parent_id
        while parent_id:
            parent = self.db.query(KnowledgeNode).filter(KnowledgeNode.id == parent_id).first()
            if not parent:
                break

            # 取所有子節點的 progress
            children = self.db.query(KnowledgeNode).filter(
                KnowledgeNode.parent_id == parent.id
            ).all()

            if not children:
                parent_id = parent.parent_id
                continue

            # 加權平均
            total_weight = 0.0
            weighted_sum = 0.0
            for child in children:
                child_mastery = self.db.query(NodeMastery).filter(
                    NodeMastery.user_id == uid, NodeMastery.node_id == child.id
                ).first()
                child_progress = float(child_mastery.mastery_rate or 0) / 100.0 if child_mastery else 0.0
                w = 1.0  # 未來可從 syllabus_topics.weight 取
                weighted_sum += child_progress * w
                total_weight += w

            parent_progress = weighted_sum / total_weight if total_weight > 0 else 0.0

            # 更新 parent mastery
            parent_mastery = self.db.query(NodeMastery).filter(
                NodeMastery.user_id == uid, NodeMastery.node_id == parent.id
            ).first()

            if not parent_mastery:
                parent_mastery = NodeMastery(
                    id=uuid.uuid4(), user_id=uid, node_id=parent.id,
                    mastery_rate=0, correct_count=0, total_count=0,
                )
                self.db.add(parent_mastery)

            parent_mastery.mastery_rate = round(parent_progress * 100, 2)
            parent_mastery.color = self._progress_to_color(parent_progress)
            parent_mastery.status = self._progress_to_status(parent_progress)

            updated.append({
                "node_id": str(parent.id),
                "new_progress": parent_progress,
                "child_count": len(children),
            })

            parent_id = parent.parent_id

        return updated

    # ── 進度稀釋（Dilution）────────────────────────────────────

    def dilute_on_topology_change(
        self,
        user_id: str,
        root_node_id: str,
        new_topic_count: int,
    ) -> dict:
        """考綱擴展時進度稀釋。

        分母變大 → progress 自然下降。
        回傳稀釋前後的差異供前端 Toast 顯示。
        """
        uid = uuid.UUID(user_id)

        # 取 root 下所有子節點
        all_children = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.parent_id == uuid.UUID(root_node_id)
        ).all()

        old_count = len(all_children) - new_topic_count
        if old_count <= 0:
            return {"diluted": False}

        # 重算 root progress（新節點 progress = 0）
        propagation = self.propagate_upward(user_id, str(all_children[0].id))

        root_update = next(
            (u for u in propagation if u["node_id"] == root_node_id), None
        )

        return {
            "diluted": True,
            "old_topic_count": old_count,
            "new_topic_count": len(all_children),
            "new_progress": root_update["new_progress"] if root_update else 0,
        }

    # ── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _progress_to_color(progress: float) -> str:
        """ progress to color。"""
        if progress >= 0.7:
            return "green"
        elif progress >= 0.4:
            return "yellow"
        elif progress > 0:
            return "red"
        return "gray"

    @staticmethod
    def _progress_to_status(progress: float) -> str:
        """ progress to status。"""
        if progress >= 0.7:
            return "MASTERED"
        elif progress >= 0.4:
            return "PENDING"
        elif progress > 0:
            return "CRITICAL"
        return "UNSEEN"
