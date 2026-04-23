"""Knowledge Canvas service — PRD-046 三層 Zoom 知識地圖.

三層結構：
- Tier 1（領域）：depth=0 節點，掌握度 = 所有後代葉節點的加權平均
- Tier 2（主題）：depth=1 節點，聚合該分支下所有葉節點掌握度
- Tier 3（節點）：depth>=2 葉節點，直接讀 NodeMastery

與 KnowledgeNavService.get_nodes_by_subject 的差異：
- 分層載入而非一次回傳整棵樹 → 大科目（200+ 節點）payload <50KB
- 聚合掌握度而非純節點掌握度 → 上層可視化意義明確
"""

import uuid

from sqlalchemy import text

from app.models.knowledge_node import KnowledgeNode
from app.models.learning_journey import LearningJourney
from app.services.base import BaseService


def _mastery_color(progress: float) -> str:
    if progress >= 0.7:
        return "green"
    if progress >= 0.4:
        return "yellow"
    if progress > 0:
        return "red"
    return "gray"


class CanvasService(BaseService):
    """PRD-046 Knowledge Canvas — 分層 zoom 視覺化資料服務。"""

    def _check_journey(self, subject_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        journey = (
            self.db.query(LearningJourney)
            .filter_by(user_id=user_id, subject_id=subject_id)
            .first()
        )
        if not journey:
            return self.error("您尚未加入此備考科目", 403)
        return None

    def _aggregated_children(
        self,
        subject_id: uuid.UUID,
        user_id: uuid.UUID,
        parent_id: uuid.UUID | None,
    ) -> list[dict]:
        """取得指定 parent 下的子節點，每個節點附帶「該分支所有葉節點」的聚合掌握度。

        使用遞迴 CTE 展開子樹，聚合 node_mastery 的 mastery_rate 平均值。
        """
        parent_clause = "parent_id IS NULL" if parent_id is None else "parent_id = :parent_id"
        params: dict = {"subject_id": subject_id, "user_id": user_id}
        if parent_id is not None:
            params["parent_id"] = parent_id

        sql = f"""
        WITH RECURSIVE direct_children AS (
            SELECT id, name, depth, sort_order, available_questions,
                   support_strength, node_source
            FROM knowledge_nodes
            WHERE subject_id = :subject_id
              AND resource_id IS NULL
              AND {parent_clause}
        ),
        descendants AS (
            -- 每個 direct_child 是自己子樹的根
            SELECT dc.id AS root_id, dc.id AS descendant_id
            FROM direct_children dc
            UNION ALL
            SELECT d.root_id, kn.id
            FROM descendants d
            JOIN knowledge_nodes kn ON kn.parent_id = d.descendant_id
            WHERE kn.resource_id IS NULL
        ),
        leaf_counts AS (
            SELECT root_id,
                   COUNT(*) FILTER (WHERE NOT EXISTS (
                       SELECT 1 FROM knowledge_nodes c
                       WHERE c.parent_id = d.descendant_id
                         AND c.resource_id IS NULL
                   )) AS leaf_count,
                   COUNT(*) AS total_count
            FROM descendants d
            GROUP BY root_id
        ),
        mastery_agg AS (
            SELECT d.root_id,
                   AVG(COALESCE(nm.mastery_rate, 0) / 100.0) AS avg_mastery,
                   COUNT(nm.node_id) AS mastered_count
            FROM descendants d
            LEFT JOIN node_mastery nm
              ON nm.node_id = d.descendant_id AND nm.user_id = :user_id
            GROUP BY d.root_id
        ),
        question_agg AS (
            SELECT d.root_id,
                   SUM(COALESCE(kn.available_questions, 0)) AS total_questions
            FROM descendants d
            JOIN knowledge_nodes kn ON kn.id = d.descendant_id
            GROUP BY d.root_id
        )
        SELECT dc.id::text, dc.name, dc.depth, dc.sort_order,
               dc.support_strength, dc.node_source,
               COALESCE(ma.avg_mastery, 0) AS avg_mastery,
               COALESCE(lc.leaf_count, 0) AS leaf_count,
               COALESCE(lc.total_count, 1) AS descendant_count,
               COALESCE(qa.total_questions, 0) AS total_questions
        FROM direct_children dc
        LEFT JOIN mastery_agg ma ON ma.root_id = dc.id
        LEFT JOIN leaf_counts lc ON lc.root_id = dc.id
        LEFT JOIN question_agg qa ON qa.root_id = dc.id
        ORDER BY dc.sort_order, dc.name
        """
        rows = self.db.execute(text(sql), params).fetchall()

        results = []
        for r in rows:
            progress = float(r.avg_mastery or 0)
            results.append({
                "id": r.id,
                "name": r.name,
                "depth": r.depth,
                "sort_order": r.sort_order or 0,
                "progress": round(progress, 4),
                "mastery_rate": int(progress * 100),
                "mastery_color": _mastery_color(progress),
                "leaf_count": r.leaf_count,
                "descendant_count": r.descendant_count,
                "available_questions": int(r.total_questions or 0),
                "support_strength": round(float(r.support_strength or 0), 3),
                "node_source": r.node_source or "user_data",
                "has_children": r.leaf_count > 0 or r.descendant_count > 1,
            })
        return results

    # ── Public API ─────────────────────────────────────────────────

    def get_tier1(self, subject_id: str, user_id: str) -> dict:
        """Tier 1 — 領域層（depth=0 節點）。"""
        sid = uuid.UUID(subject_id)
        uid = uuid.UUID(user_id)
        err = self._check_journey(sid, uid)
        if err:
            return err

        nodes = self._aggregated_children(sid, uid, parent_id=None)
        return self.ok({
            "tier": 1,
            "subject_id": subject_id,
            "parent_id": None,
            "nodes": nodes,
            "empty_reason": "no_nodes_generated" if not nodes else None,
        })

    def get_children(
        self, subject_id: str, parent_id: str, user_id: str
    ) -> dict:
        """Tier 2 / Tier 3 — 指定 parent 下的子節點。"""
        sid = uuid.UUID(subject_id)
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(parent_id)

        err = self._check_journey(sid, uid)
        if err:
            return err

        # 驗證 parent 屬於此科目（防跨科目查詢）
        parent = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.id == pid, KnowledgeNode.subject_id == sid)
            .first()
        )
        if not parent:
            return self.error("父節點不存在或不屬於此科目", 404)

        nodes = self._aggregated_children(sid, uid, parent_id=pid)
        # Tier = 子節點的 depth（DB 以 1 為根節點 depth，tier 則以 1 為領域層對外語意）
        child_depth = nodes[0]["depth"] if nodes else (parent.depth or 0) + 1
        return self.ok({
            "tier": child_depth,
            "subject_id": subject_id,
            "parent_id": parent_id,
            "parent_name": parent.name,
            "parent_depth": parent.depth or 0,
            "nodes": nodes,
            "empty_reason": "leaf_node" if not nodes else None,
        })
