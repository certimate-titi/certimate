"""
統一知識樹萃取 Service

將用戶上傳資源（resource_chunks）與考古題（historical_exams）合併為單一輸入，
由 Gemini 一次性萃取統一知識樹，並智能遷移既有 mastery 記錄。

觸發時機：
1. 資源處理完成後自動觸發
2. 知識圖譜頁面手動「重新分析」
3. 考古題初始匯入時
"""

import json
import uuid
import logging
from datetime import datetime, timezone

from google import genai
from google.genai import types as genai_types
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge_node import KnowledgeNode  # noqa: F401

log = logging.getLogger(__name__)

settings = get_settings()
_gemini_client = None
if settings.GEMINI_API_KEY:
    _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

GEMINI_MODEL = "gemini-2.5-flash"

# ─── Token 壓縮策略 ───
MAX_EXAM_QUESTIONS = 120   # 考古題最多送幾題摘要
MAX_CHUNK_CHARS = 30000    # resource_chunks 文本總字數上限
MAX_QUESTION_CHARS = 150   # 每題題幹截斷長度


def _build_unified_prompt(
    subject_name: str,
    exam_summaries: list[str],
    chunk_summaries: list[str],
    old_node_names: list[str],
) -> str:
    """
    組合統一萃取 Prompt。

    輸入：
    - exam_summaries: 考古題題幹摘要（已截斷）
    - chunk_summaries: resource_chunks 文本摘要（帶 section_title）
    - old_node_names: 既有知識節點名稱（用於 mastery 遷移對應）

    輸出 JSON Schema:
    {
      "knowledge_tree": {
        "chapters": [
          {
            "name": "章名稱",
            "description": "章說明",
            "sections": [
              {
                "name": "節名稱",
                "description": "此知識點涵蓋的核心概念",
                "exam_frequency": "high|medium|low",
                "bloom_levels": ["remember", "understand", ...]
              }
            ]
          }
        ]
      },
      "node_mapping": {
        "舊節點A": "新節點X",
        "舊節點B": "新節點Y",
        "舊節點C": null
      },
      "question_keywords": {
        "新節點X": ["關鍵詞1", "關鍵詞2"],
        "新節點Y": ["關鍵詞3"]
      }
    }
    """

    # ── 素材區塊 ──
    materials_block = ""

    if exam_summaries:
        exam_text = "\n".join(exam_summaries)
        materials_block += f"""
【考古題摘要】（共 {len(exam_summaries)} 題）
{exam_text}
"""

    if chunk_summaries:
        chunk_text = "\n".join(chunk_summaries)
        materials_block += f"""
【教材內容摘要】
{chunk_text}
"""

    if not materials_block.strip():
        raise ValueError(f"科目 {subject_name} 無任何可分析素材")

    # ── 舊節點對應區塊 ──
    mapping_block = ""
    if old_node_names:
        old_list = "\n".join(f"- {n}" for n in old_node_names)
        mapping_block = f"""
## 舊節點對應（mastery 遷移用）

以下是此科目「目前」的知識節點名稱。請在 node_mapping 中，為每個舊節點找到對應的新節點名稱。
若舊節點在新知識樹中沒有對應（被合併或移除），設為 null。

舊節點清單：
{old_list}
"""

    prompt = f"""你是一位台灣考試命題與課程設計專家。

以下是「{subject_name}」考科的所有學習素材，包含考古題和/或用戶上傳的教材內容。
請綜合分析所有素材，萃取出一份**完整統一的知識樹（考綱結構）**。

{materials_block}

## 萃取要求

1. **第一層：章（Chapter）** — 核心主題分類，**最多 6 個**（對應雷達圖六軸，嚴禁超過 6 個）
2. **第二層：節（Section）** — 每章下的子主題，每章 2-6 個
3. 每個「節」要包含：
   - name：知識點名稱（繁體中文，簡潔明確）
   - description：50-100 字說明，描述此知識點涵蓋的核心概念
   - exam_frequency：出題頻率（high/medium/low），根據考古題實際出現次數判斷；若無考古題則根據教材篇幅判斷
   - bloom_levels：常見的 Bloom 認知層次（remember/understand/apply/analyze/evaluate/create）
4. **考古題與教材內容要交叉比對**：
   - 考古題出現但教材沒提到的 → 仍要列入（依考試實際範圍）
   - 教材有但考古題沒考過的 → 仍要列入（可能是新考點）
5. **同一概念只建一個節點** — 不管來自考古題還是教材，語意相同就合併
6. 只用繁體中文
7. 不要猜測未出現的知識點

{mapping_block}

## 輸出 JSON 格式

```json
{{
  "knowledge_tree": {{
    "chapters": [
      {{
        "name": "章名稱",
        "description": "章說明",
        "sections": [
          {{
            "name": "節名稱",
            "description": "此知識點涵蓋的核心概念與考試重點",
            "exam_frequency": "high",
            "bloom_levels": ["remember", "understand"]
          }}
        ]
      }}
    ]
  }},
  {'"node_mapping": {{ "舊節點名": "新節點名或null" }},' if old_node_names else ''}
  "question_keywords": {{
    "節名稱": ["關鍵詞1", "關鍵詞2", "關鍵詞3"]
  }}
}}
```

只回傳 JSON，不要其他文字。"""

    return prompt


class UnifiedKnowledgeExtractionService:
    """統一知識樹萃取 Service。"""

    def __init__(self, db: Session):
        self.db = db
        # Prompt template service for DB-managed prompts
        self._prompt_svc = None
        try:
            from app.services.prompt_template_service import PromptTemplateService
            self._prompt_svc = PromptTemplateService(db)
        except Exception:
            pass

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """Load prompt template from DB. Returns dict or None (caller uses fallback)."""
        if not self._prompt_svc:
            return None
        try:
            result = self._prompt_svc.get_prompt_for_ai(name)
            if result.get("error"):
                return None
            if variables:
                render = self._prompt_svc.render_prompt
                result["system_prompt"] = render(result["system_prompt"], variables)
                result["user_prompt"] = render(result["user_prompt"], variables)
            return result
        except Exception:
            return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Public API
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def extract(self, subject_id: str) -> dict:
        """
        對指定科目執行統一知識樹萃取。

        Returns:
            {"ok": True, "nodes_created": int, "mastery_migrated": int}
            or {"error": True, "message": str}
        """
        sid = uuid.UUID(subject_id)

        # 1. 取得科目名稱
        subject_name = self.db.execute(
            text("SELECT name FROM subjects WHERE id = :sid"), {"sid": sid}
        ).scalar()
        if not subject_name:
            return {"error": True, "message": f"科目不存在: {subject_id}"}

        # 2. 收集素材
        exam_summaries = self._collect_exam_summaries(sid, subject_name)
        chunk_summaries = self._collect_chunk_summaries(sid)

        if not exam_summaries and not chunk_summaries:
            # No materials left — clear unified nodes and return
            self._clear_old_nodes(sid)
            return {"ok": True, "nodes_created": 0, "mastery_migrated": 0, "chunks_remapped": 0}

        # 3. 取得舊節點（用於 mastery 遷移）
        old_nodes = self._get_old_nodes(sid)
        old_node_names = [n["name"] for n in old_nodes]

        log.info(
            f"[統一萃取] {subject_name}: "
            f"考古題={len(exam_summaries)}, chunks={len(chunk_summaries)}, "
            f"舊節點={len(old_node_names)}"
        )

        # 4. 嘗試從 DB 載入 E-05 模板，fallback 到 hardcoded prompt builder
        try:
            db_prompt = self._load_prompt("syllabus_reverse_engineering", {
                "subject_name": subject_name,
                "question_count": str(len(exam_summaries)),
            })
            # DB 模板目前為簡易版，統一萃取需要完整 prompt，仍用 hardcoded builder
            prompt = _build_unified_prompt(
                subject_name, exam_summaries, chunk_summaries, old_node_names
            )
            result = self._call_gemini(prompt)
        except Exception as e:
            log.error(f"[統一萃取] Gemini 呼叫失敗: {e}")
            return {"error": True, "message": f"AI 萃取失敗: {str(e)}"}

        # 5. 儲存 node_mapping 供 mastery 遷移使用
        node_mapping = result.get("node_mapping", {})
        self._node_mapping = node_mapping

        # 6. 清除舊節點（備份 mastery）→ 寫入新節點（含 mastery 遷移）
        self._clear_old_nodes(sid)
        tree = result.get("knowledge_tree", result)
        question_keywords = result.get("question_keywords", {})
        nodes_created = self._save_knowledge_tree(sid, tree, question_keywords)

        mastery_migrated = len([b for b in getattr(self, '_mastery_backup', []) if b])

        # 7.5 重新映射 resource_chunks → 新統一節點
        chunks_remapped = self._remap_chunks_to_nodes(sid, question_keywords)

        # 8. 映射考古題到新節點
        self._map_questions_to_nodes(sid, subject_name, question_keywords)

        self.db.commit()
        log.info(
            f"[統一萃取] ✅ {subject_name}: "
            f"新節點={nodes_created}, mastery遷移={mastery_migrated}, "
            f"chunks映射={chunks_remapped}"
        )

        return {
            "ok": True,
            "nodes_created": nodes_created,
            "mastery_migrated": mastery_migrated,
            "chunks_remapped": chunks_remapped,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 素材收集
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _collect_exam_summaries(self, sid: uuid.UUID, subject_name: str) -> list[str]:
        """從 questions + historical_exams 收集考古題摘要。"""
        rows = []

        # 方法 1: 透過 exam_subject_codes 匹配（優先）
        codes = self.db.execute(
            text('SELECT exam_subject_codes FROM subjects WHERE id = :sid'),
            {'sid': sid}
        ).scalar()
        log.info(f"[萃取] subject={subject_name}, exam_subject_codes={codes}")

        if codes:
            for code in codes:
                parts = code.split(':', 1)
                if len(parts) == 2:
                    more = self.db.execute(text('''
                        SELECT q.content, q.option_a, q.option_b, q.option_c, q.option_d,
                               q.correct_answer, q.bloom_category
                        FROM questions q
                        JOIN historical_exams he ON q.historical_exam_id = he.id
                        WHERE he.exam_code = :ec AND he.subject_code = :sc
                    '''), {'ec': parts[0], 'sc': parts[1]}).fetchall()
                    log.info(f"[萃取] code={code}, found={len(more)} questions")
                    rows = list(rows) + list(more)

        # 方法 2: 透過 subject_name fallback
        if not rows:
            rows = self.db.execute(text('''
                SELECT q.content, q.option_a, q.option_b, q.option_c, q.option_d,
                       q.correct_answer, q.bloom_category
                FROM questions q
                JOIN historical_exams he ON q.historical_exam_id = he.id
                WHERE he.subject_name = :name
                ORDER BY q.question_number
            '''), {'name': subject_name}).fetchall()
            log.info(f"[萃取] subject_name fallback found={len(rows)} questions")

        summaries = []
        for i, r in enumerate(rows[:MAX_EXAM_QUESTIONS]):
            bloom = r[6] or "unknown"
            content = (r[0] or "")[:MAX_QUESTION_CHARS]
            summaries.append(f"Q{i+1}[{bloom}]: {content}")

        return summaries

    def _collect_chunk_summaries(self, sid: uuid.UUID) -> list[str]:
        """從 resource_chunks 收集教材文本摘要。"""
        self.db.execute(text("SAVEPOINT before_chunks_read"))
        try:
            rows = self.db.execute(text('''
                SELECT rc.content, rc.metadata_json, r.name as resource_name
                FROM resource_chunks rc
                JOIN resources r ON rc.resource_id = r.id
                WHERE r.subject_id = :sid
                ORDER BY r.created_at, rc.chunk_index
            '''), {'sid': sid}).fetchall()
        except Exception as e:
            # RLS policy on resource_chunks may fail without tenant context;
            # gracefully skip — extraction can proceed with exam summaries only
            log.warning(f"[萃取] 無法讀取 resource_chunks (RLS): {e}")
            self.db.execute(text("ROLLBACK TO SAVEPOINT before_chunks_read"))
            return []

        if not rows:
            return []

        summaries = []
        total_chars = 0
        for r in rows:
            if total_chars >= MAX_CHUNK_CHARS:
                break

            content = (r[0] or "")
            metadata = r[1] or {}
            section_title = metadata.get("section_title", "")
            resource_name = r[2] or ""

            # 壓縮：取前 500 字
            truncated = content[:500]
            if len(content) > 500:
                truncated += "..."

            prefix = f"[{resource_name}]"
            if section_title:
                prefix += f" {section_title}:"

            summaries.append(f"{prefix} {truncated}")
            total_chars += len(truncated)

        return summaries

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Gemini 呼叫
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _call_gemini(self, prompt: str) -> dict:
        """呼叫 Gemini API 並解析 JSON 回應。"""
        if not _gemini_client:
            raise RuntimeError("GEMINI_API_KEY not configured")

        response = _gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        return json.loads(raw)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 舊節點 & Mastery 遷移
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _get_old_nodes(self, sid: uuid.UUID) -> list[dict]:
        """取得既有的 leaf 知識節點（depth >= 2）。"""
        rows = self.db.execute(text('''
            SELECT id, name FROM knowledge_nodes
            WHERE subject_id = :sid AND parent_id IS NOT NULL
            ORDER BY sort_order
        '''), {'sid': sid}).fetchall()

        return [{"id": str(r[0]), "name": r[1]} for r in rows]

    def _clear_old_nodes(self, sid: uuid.UUID):
        """清除該科目既有的知識節點，保留 mastery 備份。"""
        now = datetime.now(timezone.utc)

        # 備份 mastery 到暫存表（用 JSON 欄位存在 memo 中）
        mastery_backup = self.db.execute(text('''
            SELECT nm.user_id, kn.name, nm.base_mastery, nm.ease_factor,
                   nm.last_tested_at, nm.next_review_at, nm.status,
                   nm.correct_count, nm.total_count, nm.mastery_rate
            FROM node_mastery nm
            JOIN knowledge_nodes kn ON nm.node_id = kn.id
            WHERE kn.subject_id = :sid
        '''), {'sid': sid}).fetchall()

        self._mastery_backup = [
            {
                "user_id": str(r[0]), "node_name": r[1],
                "base_mastery": r[2], "ease_factor": r[3],
                "last_tested_at": r[4], "next_review_at": r[5],
                "status": r[6], "correct_count": r[7],
                "total_count": r[8], "mastery_rate": float(r[9]) if r[9] else 0,
            }
            for r in mastery_backup
        ]

        # 解除所有 FK 引用
        node_subq = 'SELECT id FROM knowledge_nodes WHERE subject_id = :sid'
        self.db.execute(text(f'UPDATE questions SET node_id = NULL WHERE node_id IN ({node_subq})'), {'sid': sid})
        self.db.execute(text(f'UPDATE questions SET suggested_node_id = NULL WHERE suggested_node_id IN ({node_subq})'), {'sid': sid})
        # resource_chunks has RLS policy; use savepoint to avoid rolling back prior work
        self.db.execute(text("SAVEPOINT before_chunks"))
        try:
            self.db.execute(text(f'UPDATE resource_chunks SET node_id = NULL WHERE node_id IN ({node_subq})'), {'sid': sid})
        except Exception:
            self.db.execute(text("ROLLBACK TO SAVEPOINT before_chunks"))
        self.db.execute(text(f'DELETE FROM node_mastery WHERE node_id IN ({node_subq})'), {'sid': sid})
        self.db.execute(text(f'DELETE FROM question_stats WHERE node_id IN ({node_subq})'), {'sid': sid})
        self.db.execute(text(f'DELETE FROM merge_conflicts WHERE existing_node_id IN ({node_subq})'), {'sid': sid})

        # 刪除節點（先子後父）
        self.db.execute(text('DELETE FROM knowledge_nodes WHERE subject_id = :sid AND parent_id IS NOT NULL'), {'sid': sid})
        self.db.execute(text('DELETE FROM knowledge_nodes WHERE subject_id = :sid'), {'sid': sid})

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 寫入新節點
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _save_knowledge_tree(self, sid: uuid.UUID, tree: dict, question_keywords: dict) -> int:
        """寫入新的知識樹。回傳建立的節點數。"""
        chapters = tree.get("chapters", [])
        now = datetime.now(timezone.utc)
        total = 0

        for ch_idx, chapter in enumerate(chapters):
            chapter_id = uuid.uuid4()
            ch_desc = chapter.get("description", "")

            self.db.execute(text("""
                INSERT INTO knowledge_nodes (id, subject_id, parent_id, name, depth, sort_order,
                    source_origin, source_text, exam_frequency, available_questions, created_at)
                VALUES (:id, :sid, NULL, :name, 1, :sort, 'ai_unified', :text, 'medium', 0, :now)
            """), {
                "id": chapter_id, "sid": sid, "name": chapter["name"],
                "sort": ch_idx, "text": f"# {chapter['name']}\n\n{ch_desc}", "now": now,
            })
            total += 1

            for sec_idx, section in enumerate(chapter.get("sections", [])):
                section_id = uuid.uuid4()
                sec_desc = section.get("description", "")
                freq = section.get("exam_frequency", "medium")
                bloom_levels = section.get("bloom_levels", [])

                source_text = f"# {section['name']}\n\n{sec_desc}"
                if bloom_levels:
                    source_text += f"\n\n## 常見 Bloom 層次\n{', '.join(bloom_levels)}"

                # 加入 question_keywords 到 source_text
                keywords = question_keywords.get(section["name"], [])
                if keywords:
                    source_text += f"\n\n## 關鍵詞\n{', '.join(keywords)}"

                self.db.execute(text("""
                    INSERT INTO knowledge_nodes (id, subject_id, parent_id, name, depth, sort_order,
                        source_origin, source_text, exam_frequency, available_questions, created_at)
                    VALUES (:id, :sid, :pid, :name, 2, :sort, 'ai_unified', :text, :freq, 0, :now)
                """), {
                    "id": section_id, "sid": sid, "pid": chapter_id,
                    "name": section["name"], "sort": sec_idx,
                    "text": source_text, "freq": freq, "now": now,
                })
                total += 1

        # 遷移 mastery backup 到新節點
        self._restore_mastery_backup(sid)

        return total

    def _restore_mastery_backup(self, sid: uuid.UUID):
        """將備份的 mastery 記錄遷移到新節點（依名稱對應）。"""
        if not hasattr(self, '_mastery_backup') or not self._mastery_backup:
            return

        # 建立新節點名 → ID 對照
        new_nodes = self.db.execute(text('''
            SELECT id, name FROM knowledge_nodes
            WHERE subject_id = :sid AND parent_id IS NOT NULL
        '''), {'sid': sid}).fetchall()
        new_name_to_id = {r[1]: r[0] for r in new_nodes}

        migrated = 0
        for backup in self._mastery_backup:
            node_name = backup["node_name"]

            # 先嘗試精確匹配
            new_node_id = new_name_to_id.get(node_name)

            # 再嘗試從 node_mapping 對應
            if not new_node_id and hasattr(self, '_node_mapping'):
                mapped_name = self._node_mapping.get(node_name)
                if mapped_name:
                    new_node_id = new_name_to_id.get(mapped_name)

            if not new_node_id:
                continue

            # 檢查是否已存在（避免重複）
            exists = self.db.execute(text('''
                SELECT 1 FROM node_mastery
                WHERE user_id = :uid AND node_id = :nid
            '''), {'uid': backup["user_id"], 'nid': new_node_id}).scalar()

            if exists:
                # 更新（保留較高的 mastery）
                self.db.execute(text('''
                    UPDATE node_mastery SET
                        base_mastery = GREATEST(base_mastery, :bm),
                        ease_factor = :ef,
                        last_tested_at = :lt,
                        next_review_at = :nr,
                        status = :st,
                        correct_count = correct_count + :cc,
                        total_count = total_count + :tc
                    WHERE user_id = :uid AND node_id = :nid
                '''), {
                    'uid': backup["user_id"], 'nid': new_node_id,
                    'bm': backup["base_mastery"] or 0,
                    'ef': backup["ease_factor"] or 2.5,
                    'lt': backup["last_tested_at"],
                    'nr': backup["next_review_at"],
                    'st': backup["status"] or "UNSEEN",
                    'cc': backup["correct_count"] or 0,
                    'tc': backup["total_count"] or 0,
                })
            else:
                self.db.execute(text('''
                    INSERT INTO node_mastery (id, user_id, node_id,
                        base_mastery, ease_factor, last_tested_at, next_review_at,
                        status, correct_count, total_count, mastery_rate)
                    VALUES (:id, :uid, :nid, :bm, :ef, :lt, :nr, :st, :cc, :tc, :mr)
                '''), {
                    'id': uuid.uuid4(),
                    'uid': backup["user_id"], 'nid': new_node_id,
                    'bm': backup["base_mastery"] or 0,
                    'ef': backup["ease_factor"] or 2.5,
                    'lt': backup["last_tested_at"],
                    'nr': backup["next_review_at"],
                    'st': backup["status"] or "UNSEEN",
                    'cc': backup["correct_count"] or 0,
                    'tc': backup["total_count"] or 0,
                    'mr': backup["mastery_rate"] or 0,
                })
            migrated += 1

        log.info(f"[mastery 遷移] ✅ {migrated}/{len(self._mastery_backup)} 筆成功遷移")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Chunk → 統一節點映射
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _remap_chunks_to_nodes(self, sid: uuid.UUID, question_keywords: dict) -> int:
        """將該科目下所有 resource_chunks 重新映射到統一知識節點。

        映射策略（依優先序）：
        1. chunk 的 section_title 完全匹配節點名稱
        2. 節點名稱出現在 chunk section_title 中（子字串匹配）
        3. 加權 keyword 計分：節點名稱 + question_keywords + source_text 關鍵詞
           在 chunk content 中出現次數 × 關鍵詞長度（越長越精確）
        未匹配的 chunk 歸入第一個 section（fallback）。
        """
        import re as _re

        # 取得新的統一節點（含 source_text 以提取關鍵詞）
        nodes = self.db.execute(text('''
            SELECT id, name, parent_id, depth, source_text FROM knowledge_nodes
            WHERE subject_id = :sid AND source_origin = 'ai_unified'
            ORDER BY depth, sort_order
        '''), {'sid': sid}).fetchall()

        if not nodes:
            return 0

        section_nodes = [(r[0], r[1], r[2], r[4]) for r in nodes if r[3] == 2]
        if not section_nodes:
            return 0

        fallback_node_id = section_nodes[0][0]
        name_to_id: dict[str, uuid.UUID] = {name: nid for nid, name, _, _ in section_nodes}

        # 建立每個節點的關鍵詞集合（來源：節點名 + question_keywords + source_text 中的關鍵詞）
        node_kw_sets: dict[uuid.UUID, set[str]] = {}
        for nid, name, _, source_text in section_nodes:
            keywords: set[str] = {name}

            # 從 question_keywords 加入
            qk = question_keywords.get(name, [])
            for kw in qk:
                kw = kw.strip()
                if len(kw) >= 2:
                    keywords.add(kw)

            # 從 source_text 的「關鍵詞」區段提取
            if source_text:
                kw_match = _re.search(r'## 關鍵詞\n(.+)', source_text)
                if kw_match:
                    for kw in _re.split(r'[,、，]', kw_match.group(1)):
                        kw = kw.strip()
                        if len(kw) >= 2:
                            keywords.add(kw)

            node_kw_sets[nid] = keywords

        # 取得此科目所有 chunks
        self.db.execute(text("SAVEPOINT before_chunk_remap"))
        try:
            chunks = self.db.execute(text('''
                SELECT rc.id, rc.metadata_json, rc.content
                FROM resource_chunks rc
                JOIN resources r ON rc.resource_id = r.id
                WHERE r.subject_id = :sid
            '''), {'sid': sid}).fetchall()
        except Exception as e:
            log.warning(f"[chunk映射] 無法讀取 chunks (RLS): {e}")
            self.db.execute(text("ROLLBACK TO SAVEPOINT before_chunk_remap"))
            return 0

        if not chunks:
            return 0

        mapped = 0
        for chunk_id, metadata, content in chunks:
            meta = metadata or {}
            section_title = meta.get("section_title", "")
            content_text = content or ""

            best_node_id = None

            # 策略 1: section_title 精確匹配節點名
            if section_title and section_title in name_to_id:
                best_node_id = name_to_id[section_title]

            # 策略 2: 節點名稱是 section_title 的子字串
            if not best_node_id and section_title:
                for node_name, nid in name_to_id.items():
                    if node_name in section_title or section_title in node_name:
                        best_node_id = nid
                        break

            # 策略 3: 加權 keyword 計分（出現次數 × 關鍵詞長度）
            if not best_node_id:
                scores: dict[uuid.UUID, int] = {}
                for nid, keywords in node_kw_sets.items():
                    score = 0
                    for kw in keywords:
                        count = content_text.count(kw)
                        if count > 0:
                            score += count * len(kw)
                    if score > 0:
                        scores[nid] = score
                if scores:
                    best_node_id = max(scores, key=scores.get)  # type: ignore[arg-type]

            # Fallback
            if not best_node_id:
                best_node_id = fallback_node_id

            self.db.execute(text('''
                UPDATE resource_chunks SET node_id = :nid WHERE id = :cid
            '''), {'nid': best_node_id, 'cid': chunk_id})
            mapped += 1

        log.info(f"[chunk映射] ✅ {mapped}/{len(chunks)} chunks 已映射到統一節點")
        return mapped

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 題目映射
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _map_questions_to_nodes(self, sid: uuid.UUID, subject_name: str, question_keywords: dict):
        """用 Gemini 回傳的 question_keywords 將考古題映射到新節點。"""
        # 取得新的 leaf 節點
        leaf_nodes = self.db.execute(text('''
            SELECT id, name FROM knowledge_nodes
            WHERE subject_id = :sid AND parent_id IS NOT NULL
        '''), {'sid': sid}).fetchall()

        if not leaf_nodes:
            return

        node_name_to_id = {r[1]: r[0] for r in leaf_nodes}

        # 建立 keyword → node_id 索引
        keyword_index: list[tuple[str, uuid.UUID, list[str]]] = []
        for node_name, keywords in question_keywords.items():
            nid = node_name_to_id.get(node_name)
            if nid:
                keyword_index.append((node_name, nid, keywords or []))

        # 取得所有未映射的考古題
        questions = self.db.execute(text('''
            SELECT q.id, q.content, q.option_a, q.option_b, q.option_c, q.option_d
            FROM questions q
            JOIN historical_exams he ON q.historical_exam_id = he.id
            WHERE he.subject_name = :name AND q.node_id IS NULL
        '''), {'name': subject_name}).fetchall()

        # 也查 exam_subject_codes
        codes = self.db.execute(
            text('SELECT exam_subject_codes FROM subjects WHERE id = :sid'),
            {'sid': sid}
        ).scalar()
        if codes:
            for code in (codes or []):
                parts = code.split(':', 1)
                if len(parts) == 2:
                    more = self.db.execute(text('''
                        SELECT q.id, q.content, q.option_a, q.option_b, q.option_c, q.option_d
                        FROM questions q
                        JOIN historical_exams he ON q.historical_exam_id = he.id
                        WHERE he.exam_code = :ec AND he.subject_code = :sc AND q.node_id IS NULL
                    '''), {'ec': parts[0], 'sc': parts[1]}).fetchall()
                    questions = list(questions) + list(more)

        mapped = 0
        leaf_list = list(node_name_to_id.values())

        for i, q in enumerate(questions):
            full_text = f"{q[1] or ''} {q[2] or ''} {q[3] or ''} {q[4] or ''} {q[5] or ''}"

            best_node_id = None
            best_score = 0

            for node_name, nid, keywords in keyword_index:
                score = 0
                # 關鍵詞匹配
                for kw in keywords:
                    if kw and kw in full_text:
                        score += 2
                # 節點名稱匹配
                for char in node_name:
                    if len(char.strip()) > 0 and char in full_text:
                        score += 0.5
                if node_name in full_text:
                    score += 5

                if score > best_score:
                    best_score = score
                    best_node_id = nid

            # Fallback: round-robin
            if not best_node_id:
                best_node_id = leaf_list[i % len(leaf_list)]

            self.db.execute(
                text('UPDATE questions SET node_id = :nid WHERE id = :qid'),
                {'nid': best_node_id, 'qid': q[0]}
            )
            mapped += 1

        # 更新 available_questions 計數
        self.db.execute(text('''
            UPDATE knowledge_nodes SET available_questions = COALESCE(sub.cnt, 0)
            FROM (
                SELECT q.node_id, COUNT(*) as cnt FROM questions q
                WHERE q.node_id IS NOT NULL GROUP BY q.node_id
            ) sub WHERE knowledge_nodes.id = sub.node_id
            AND knowledge_nodes.subject_id = :sid
        '''), {'sid': sid})

        log.info(f"[題目映射] ✅ {mapped} 題映射完成")
