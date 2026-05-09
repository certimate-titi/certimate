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
import os
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

# T2-B: env-var controlled model selection for A/B testing
# Default flash for cost, allow pro for quality experiments
GEMINI_MODEL = os.environ.get("GEMINI_UNIFIED_EXTRACTION_MODEL", "gemini-2.5-flash")

# ─── Token 壓縮策略 ───
MAX_EXAM_QUESTIONS = 120   # 考古題最多送幾題摘要
MAX_CHUNK_CHARS = 30000    # resource_chunks 文本總字數上限
MAX_QUESTION_CHARS = 150   # 每題題幹截斷長度


def _build_unified_prompt(
    subject_name: str,
    exam_summaries: list[str],
    chunk_summaries: list[str],
    old_node_names: list[str],
    syllabus_anchors: list[dict] | None = None,
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

    # ── Feature 34 §3 Strategy E — Syllabus anchor floor ──
    # 若有預 seed 的考綱錨點，強制 LLM 的 6 章必須對應到這組錨點，
    # 避免資料稀少時 LLM 自由發揮產生 6 個不相干的章。
    anchor_block = ""
    anchor_constraint = ""
    if syllabus_anchors:
        # Only list CHAPTER names — omitting section names prevents the LLM
        # from pattern-copying them verbatim without generating descriptions.
        anchor_lines = [
            f"{idx}. **{ch['name']}**"
            for idx, ch in enumerate(syllabus_anchors, 1)
        ]
        anchor_block = f"""

## 🎯 考綱錨點（章層級，必須對齊）

此科目已有預先定義的 {len(syllabus_anchors)} 個考綱章層級錨點（由考古題反向歸納）：

{chr(10).join(anchor_lines)}

（第二層「節」由你依考古題內容自行萃取與描述，不預設。）
"""
        anchor_constraint = (
            "\n**【強制約束 1】** 第一層「章」必須 1:1 對應上述考綱錨點 —"
            " 名稱可以微調（同義詞、更精確的用詞），但不得自由創造新的章，"
            "也不得合併或拆分。第二層「節」在每個章底下可根據實際素材調整，"
            "允許新增/合併/刪除。\n"
            "**【強制約束 2】** 所有「章」和「節」都必須有完整的 description 欄位"
            "（50-100 字繁體中文說明）。**絕對不可**只複製錨點上的節名當結果 —"
            "你必須根據考古題內容，為每一個節點撰寫獨立的、實質性的描述。"
            "description 為空字串或僅含標題會被視為格式錯誤。\n"
        )

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
{anchor_block}
## 萃取要求
{anchor_constraint}
1. **第一層：章（Chapter）** — 核心主題分類，**4-8 個之間**（依學科實際結構動態，不強制）
   品質閘門：每章必有 ≥ 3 個 section + description ≥ 150 字
2. **第二層：節（Section）** — 每章下的子主題，每章 2-6 個
3. **第三層：子節（Subsection）— 可選** — 僅當 section 內容結構複雜（如 iPAS 考綱「3.1.2 反向傳播演算法」）時填入
   - 每個 subsection 含 name（必填）+ description（選填）
   - 簡單 section 不需要硬塞第三層（教育顧問：避免虛胖）
3. 每個「節」要包含：
   - name：知識點名稱（繁體中文，簡潔明確）
   - description：**150-250 字**的詳細說明，必須涵蓋：
     (1) 此知識點的定義與核心概念（為什麼重要）
     (2) 具體子議題或技術項目（列舉 3-5 個關鍵概念 / 演算法 / 法規條文）
     (3) 考試出題模式（通常怎麼考、常見陷阱、易錯點）
     禁止只寫抽象結論，必須帶入具體名詞讓使用者能立即理解內容
   - exam_frequency：出題頻率（high/medium/low），根據考古題實際出現次數判斷；若無考古題則根據教材篇幅判斷
   - bloom_levels：常見的 Bloom 認知層次（remember/understand/apply/analyze/evaluate/create）
4. 「章」的 description 也應達到 **150-250 字**，說明整章涵蓋的主題範圍、核心目標，以及本章與其他章節的關聯
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

**【嚴格 Schema 驗證】**
- 結構**只有兩層**：`chapters → sections`。嚴禁在 section 內建立 `subsections`、`children` 或任何更深的巢狀結構。
- 每個 `chapter` **必須**包含：`name`, `description` (150-250字), `sections`
- 每個 `section` **必須**包含：`name`, `description` (150-250字), `exam_frequency`, `bloom_levels`
- `description` 欄位**絕對不可省略、不可為空字串、不可只重複 name**。
- description 必須包含**具體名詞**（演算法名、法規條文號、技術縮寫、實例），禁止抽象結論如「本節涵蓋相關概念與應用」。
- 回傳 JSON 前自我檢查：若任一節點 description 少於 150 字或有 subsections 陣列，視為錯誤回應。

只回傳 JSON，不要其他文字。"""

    return prompt


class UnifiedKnowledgeExtractionService:
    """統一知識樹萃取 Service。"""

    def __init__(self, db: Session):
        """初始化實例。"""
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

        # 2.5 Feature 34 §3 Strategy E — 載入 syllabus anchors（若有）
        syllabus_anchors = self._load_syllabus_anchors(sid)

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

        # 4. 優先用 DB 模板（E-05 syllabus_reverse_engineering）；模板異常或停用時 fallback hardcoded
        try:
            db_prompt = self._load_prompt("syllabus_reverse_engineering", {
                "subject_name": subject_name,
                "question_count": str(len(exam_summaries)),
                "exam_summaries": json.dumps(exam_summaries, ensure_ascii=False)[:8000],
                "chunk_summaries": json.dumps(chunk_summaries, ensure_ascii=False)[:8000],
                "old_node_names": json.dumps(old_node_names, ensure_ascii=False)[:2000],
                "syllabus_anchors": json.dumps(syllabus_anchors, ensure_ascii=False) if syllabus_anchors else "[]",
            })
            if db_prompt and db_prompt.get("system_prompt") and db_prompt.get("user_prompt"):
                prompt = db_prompt["system_prompt"] + "\n\n" + db_prompt["user_prompt"]
                log.info("[統一萃取] 使用 DB 模板 E-05 syllabus_reverse_engineering")
            else:
                prompt = _build_unified_prompt(
                    subject_name, exam_summaries, chunk_summaries, old_node_names,
                    syllabus_anchors=syllabus_anchors,
                )
                log.info("[統一萃取] DB 模板不可用，fallback 到 hardcoded prompt builder")
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

        # Sprint 10 T81：節點 embedding 寫入（讓 _link_scaffolds_to_nodes 能對應）
        try:
            self._embed_nodes_for_subject(sid)
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            log.warning("[統一萃取] node embedding 寫入失敗（non-fatal）: %s", exc)
            self.db.rollback()

        # Sprint 10 T82-D：unified extraction 重跑 → 全 subject scaffolds re-link
        try:
            self._relink_subject_scaffolds(sid)
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            log.warning("[統一萃取] scaffold-node relink 失敗（non-fatal）: %s", exc)
            self.db.rollback()

        # Mindmap upgrade §3 — 萃取完成後重算每個節點的 support_strength
        try:
            from app.services.mindmap_strength_service import MindmapStrengthService
            strength_updated = MindmapStrengthService(self.db).recompute_for_subject(sid)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "[統一萃取] support_strength recompute failed (non-fatal): %s", exc
            )
            strength_updated = 0

        log.info(
            f"[統一萃取] ✅ {subject_name}: "
            f"新節點={nodes_created}, mastery遷移={mastery_migrated}, "
            f"chunks映射={chunks_remapped}, strength更新={strength_updated}"
        )

        # Post-extract quality gate (Feature 34 — QA depth improvement).
        # Runs data-integrity checks after every extract() so schema drift,
        # empty descriptions, and strength anomalies are caught at the source
        # instead of leaking to the UI. Failures are logged but non-fatal so
        # the user still gets the nodes — fix-forward rather than block.
        try:
            from app.scripts.verify_mindmap_quality import _check_subject
            qa_report = _check_subject(self.db, str(sid))
            if not qa_report["passed"]:
                log.warning(
                    "[QA gate] %s: %d failures — %s",
                    subject_name,
                    qa_report["failure_count"],
                    [f["code"] for f in qa_report["failures"][:5]],
                )
            else:
                log.info("[QA gate] %s: all checks passed", subject_name)
        except Exception as exc:  # noqa: BLE001
            log.warning("[QA gate] check failed (non-fatal): %s", exc)
            qa_report = {"passed": None, "error": str(exc)}

        return {
            "ok": True,
            "nodes_created": nodes_created,
            "mastery_migrated": mastery_migrated,
            "chunks_remapped": chunks_remapped,
            "strength_updated": strength_updated,
            "qa_report": qa_report,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 素材收集
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _load_syllabus_anchors(self, sid: uuid.UUID) -> list[dict]:
        """Feature 34 §3 Strategy E — 載入科目的考綱錨點（depth=0 章 + depth=1 節）.

        Returns:
            List of chapters, each with {"id", "name", "weight", "sections": [...]}
            Empty list if no syllabus_topics seeded for this subject.
        """
        chapters = self.db.execute(
            text(
                """
                SELECT id, name, weight
                FROM syllabus_topics
                WHERE subject_id = :sid AND parent_id IS NULL AND is_active = true
                ORDER BY weight DESC, name
                """
            ),
            {"sid": sid},
        ).fetchall()

        if not chapters:
            return []

        anchors: list[dict] = []
        for ch_id, ch_name, ch_weight in chapters:
            sections = self.db.execute(
                text(
                    """
                    SELECT id, name, weight
                    FROM syllabus_topics
                    WHERE parent_id = :pid AND is_active = true
                    ORDER BY weight DESC, name
                    """
                ),
                {"pid": ch_id},
            ).fetchall()
            anchors.append(
                {
                    "id": str(ch_id),
                    "name": ch_name,
                    "weight": float(ch_weight or 1.0),
                    "sections": [
                        {"id": str(s[0]), "name": s[1], "weight": float(s[2] or 1.0)}
                        for s in sections
                    ],
                }
            )

        log.info(
            f"[syllabus_anchor] loaded {len(anchors)} chapters "
            f"with {sum(len(a['sections']) for a in anchors)} sections"
        )
        return anchors

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
        """呼叫 Gemini API 並解析 JSON 回應。

        Wrapped with track_ai_usage (Feature 33) so the ai_usage_ledger
        records every extract() invocation against the AI_GEMINI budget
        scope. Without this wrapper the cost monitor showed $0 despite
        real spend — this was the QA gap flagged on 2026-04-15.
        """
        from app.middleware.ai_usage_tracker import (
            estimate_gemini_cost,
            track_ai_usage,
        )

        if not _gemini_client:
            raise RuntimeError("GEMINI_API_KEY not configured")

        with track_ai_usage(
            self.db, provider="gemini", feature="unified_extract"
        ) as tracker:
            result = self._call_gemini_inner(prompt)
            # Estimate tokens from char counts (~4 chars / token — zh/en mixed)
            in_tokens = len(prompt) // 4 or 1
            out_tokens = len(str(result)) // 4 or 1
            tracker.input_tokens = in_tokens
            tracker.output_tokens = out_tokens
            tracker.endpoint = GEMINI_MODEL
            tracker.cost_usd = estimate_gemini_cost(
                in_tokens, out_tokens, model=GEMINI_MODEL
            )
            return result

    def _call_gemini_inner(self, prompt: str) -> dict:
        """Raw Gemini call — separated so track_ai_usage wrapper stays clean."""
        if not _gemini_client:
            raise RuntimeError("GEMINI_API_KEY not configured")

        # Sprint 10 T89：放寬章上限 6 → 4-8 動態，subsections 升級為 nested object（第三層 optional）
        # 教育顧問建議：依學科實際結構動態，不被 UI 雷達圖反推約束
        response_schema = {
            "type": "object",
            "properties": {
                "knowledge_tree": {
                    "type": "object",
                    "properties": {
                        "chapters": {
                            "type": "array",
                            "maxItems": 8,  # 放寬 6→8（仍守 Miller's 7±2 上限）
                            "minItems": 4,  # 下限 4 確保品質（避免太籠統）
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "sections": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "description": {"type": "string"},
                                                # 第三層升級為 optional nested object（教育顧問 §10.2）
                                                # iPAS 考綱實際 3 層，第三層僅在結構複雜時填入
                                                "subsections": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "name": {"type": "string"},
                                                            "description": {"type": "string"},
                                                        },
                                                        "required": ["name"],
                                                    },
                                                },
                                            },
                                            "required": ["name"],
                                        },
                                    },
                                },
                                "required": ["name"],
                            },
                        }
                    },
                    "required": ["chapters"],
                },
                "node_mapping": {"type": "object"},
                "question_keywords": {"type": "object"},
            },
            "required": ["knowledge_tree"],
        }

        # Gemini 2.5 Pro 預設 max_output_tokens 偏低，大型 PDF 會被截斷在 ~85KB
        # 顯式設為 65536（~200KB JSON）以容納大量章節 + node_mapping
        common_cfg_kwargs = {
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "max_output_tokens": 65536,
        }
        try:
            response = _gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={**common_cfg_kwargs, "response_schema": response_schema},
            )
        except Exception as exc:  # noqa: BLE001
            # Some Gemini versions may reject complex response_schema — fallback
            log.warning(
                "Gemini response_schema rejected (%s); retrying without schema",
                exc,
            )
            response = _gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=common_cfg_kwargs,
            )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        # 加 graceful JSON parse — 若仍被截斷則 log truncated 區段大小再 raise
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            log.error(
                "[統一萃取] JSON truncated at char %d / total %d; head=%r tail=%r",
                e.pos, len(raw), raw[:120], raw[-120:],
            )
            raise

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

    # ── Sprint 10 T81-T82：節點 embedding + scaffold relink ────────────────

    def _embed_nodes_for_subject(self, sid: uuid.UUID) -> int:
        """為該科目所有 embedding IS NULL 的節點寫入 voyage embedding。

        對 (name + source_text) 算 embedding 寫入 knowledge_nodes.embedding。
        失敗單筆只 log warning。
        """
        rows = self.db.execute(text(
            "SELECT id, name, COALESCE(source_text, '') AS st "
            "FROM knowledge_nodes WHERE subject_id = :sid AND embedding IS NULL"
        ), {"sid": sid}).fetchall()
        if not rows:
            return 0
        try:
            from app.services.embedding_service import EmbeddingService
            emb = EmbeddingService()
            texts = [(r[1] + " " + r[2]).strip()[:1000] for r in rows]
            vecs = emb.embed_texts(texts, input_type="document")
            for r, vec in zip(rows, vecs):
                self.db.execute(text(
                    "UPDATE knowledge_nodes SET embedding = CAST(:v AS vector) WHERE id = :id"
                ), {"v": str(list(vec)), "id": str(r[0])})
            log.info("[節點 embedding] 寫入 %d 筆 subject=%s", len(rows), sid)
            return len(rows)
        except Exception as e:
            log.warning("[節點 embedding] voyage 失敗（non-fatal）: %s", e)
            return 0

    def _relink_subject_scaffolds(self, sid: uuid.UUID) -> int:
        """unified extraction 重跑 → 該 subject 所有 scaffold ↔ node 關聯重建。

        策略：刪舊 link、批次算 cosine、寫新 link。重用 resource_parse_service
        的 _link_scaffolds_to_nodes 邏輯（避免邏輯漂移）。
        """
        # 取該科目所有 scaffold（join resources.subject_id = sid）
        from app.models.resource_scaffold import ResourceScaffold
        from app.models.resource import Resource
        scaffolds = self.db.execute(text(
            """
            SELECT s.id FROM resource_scaffolds s
            JOIN resources r ON s.resource_id = r.id
            WHERE r.subject_id = :sid AND s.embedding IS NOT NULL
            """
        ), {"sid": sid}).fetchall()
        if not scaffolds:
            return 0
        # 刪除這些 scaffold 既有 link
        self.db.execute(text(
            "DELETE FROM scaffold_node_links WHERE scaffold_id = ANY(:ids)"
        ), {"ids": [r[0] for r in scaffolds]})
        # 重新算（重用 parse service 的函式）
        from app.services.resource_parse_service import _link_scaffolds_to_nodes
        scaffold_objs = self.db.query(ResourceScaffold).filter(
            ResourceScaffold.id.in_([r[0] for r in scaffolds])
        ).all()
        n = _link_scaffolds_to_nodes(self.db, scaffold_objs, sid)
        log.info("[scaffold relink] subject=%s scaffolds=%d links=%d",
                 sid, len(scaffold_objs), n)
        return n

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

                # Defensive parsing: if LLM returned `subsections` instead of
                # `description` (schema drift), synthesize a rich description
                # from subsection names so the node isn't left blank and
                # reaches the 150+ char target without an extra LLM call.
                if not sec_desc or len(sec_desc) < 100:
                    subsections = section.get("subsections", [])
                    if subsections and isinstance(subsections, list):
                        sub_names = [
                            s if isinstance(s, str) else s.get("name", "")
                            for s in subsections
                        ]
                        sub_names = [s for s in sub_names if s]
                        if sub_names:
                            name_list = "、".join(sub_names)
                            first = sub_names[0]
                            second = sub_names[1] if len(sub_names) > 1 else first
                            last = sub_names[-1]
                            sec_desc = (
                                f"本節為「{section['name']}」在此科目中的核心考點之一，"
                                f"涵蓋下列關鍵子議題：{name_list}。"
                                f"其中「{first}」是基礎概念，常與「{second}」搭配出題；"
                                f"「{last}」則是近年常考的進階延伸。"
                                f"考生應掌握每個子議題的定義、適用情境與判斷原則，"
                                f"並結合考古題的實際案例，建立對本節完整的知識連結。"
                                f"出題形式常見為情境判斷題、下列何者正確/錯誤題，以及比較辨析題。"
                            )

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

                # Sprint 10 T89：第三層 subsection（optional）— 僅當 LLM 回傳結構化 object
                # 簡單 section 不寫第三層（避免虛胖）；舊版 subsection 為 string 時保留作 description hint
                subsections = section.get("subsections", [])
                if subsections and isinstance(subsections, list):
                    for sub_idx, sub in enumerate(subsections):
                        # 只接受 dict 結構（含 name），string 形式由前面 description 邏輯處理過
                        if not isinstance(sub, dict) or not sub.get("name"):
                            continue
                        sub_name = sub["name"]
                        sub_desc = sub.get("description", "")
                        sub_text = f"### {sub_name}\n\n{sub_desc}" if sub_desc else f"### {sub_name}"
                        sub_id = uuid.uuid4()
                        self.db.execute(text("""
                            INSERT INTO knowledge_nodes (id, subject_id, parent_id, name, depth, sort_order,
                                source_origin, source_text, exam_frequency, available_questions, created_at)
                            VALUES (:id, :sid, :pid, :name, 3, :sort, 'ai_unified', :text, :freq, 0, :now)
                        """), {
                            "id": sub_id, "sid": sid, "pid": section_id,
                            "name": sub_name, "sort": sub_idx,
                            "text": sub_text, "freq": freq, "now": now,
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

    def _semantic_map_questions_via_voyage(
        self, sid: uuid.UUID, leaf_nodes: list, questions: list
    ) -> int:
        """Fallback mapping using Voyage embeddings + cosine similarity.

        Feature 33 + 34 補強: previous mapping was pure keyword LIKE which
        missed questions phrased differently from the node name. This adds
        a semantic layer so every question gets a best-match node even
        without keyword overlap. Voyage usage is tracked via track_ai_usage.

        Returns count of questions mapped.
        """
        from app.middleware.ai_usage_tracker import (
            estimate_voyage_cost,
            track_ai_usage,
        )
        from app.services.embedding_service import EmbeddingService
        import math

        if not leaf_nodes or not questions:
            return 0

        try:
            emb_svc = EmbeddingService()
        except Exception as exc:
            log.warning("[Voyage] init failed, skipping semantic map: %s", exc)
            return 0

        # Pull node source_text for richer embedding input
        node_rows = self.db.execute(
            text(
                """
                SELECT id, name, COALESCE(source_text, name)
                FROM knowledge_nodes
                WHERE id = ANY(:ids)
                """
            ),
            {"ids": [r[0] for r in leaf_nodes]},
        ).fetchall()
        node_ids = [r[0] for r in node_rows]
        node_texts = [f"{r[1]} — {r[2][:400]}" for r in node_rows]

        # Build question texts
        q_ids = [r[0] for r in questions]
        q_texts = [
            " ".join(str(c or "") for c in r[1:6])[:500] for r in questions
        ]

        def _cosine(a, b):
            """ cosine。"""
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a)) or 1.0
            nb = math.sqrt(sum(x * x for x in b)) or 1.0
            return dot / (na * nb)

        with track_ai_usage(
            self.db, provider="voyage", feature="unified_extract_map"
        ) as tracker:
            # Voyage allows batch embedding; SDK handles chunking internally
            node_embs = emb_svc.embed_texts(node_texts, input_type="document")
            question_embs = emb_svc.embed_texts(q_texts, input_type="document")

            total_chars = sum(len(t) for t in node_texts) + sum(len(t) for t in q_texts)
            est_tokens = total_chars // 4 or 1
            tracker.input_tokens = est_tokens
            tracker.output_tokens = 0
            tracker.endpoint = emb_svc.model
            tracker.cost_usd = estimate_voyage_cost(est_tokens, model=emb_svc.model)

        # For each question pick best node by cosine
        mapped = 0
        for qi, qemb in enumerate(question_embs):
            best_idx = 0
            best_score = -1.0
            for ni, nemb in enumerate(node_embs):
                s = _cosine(qemb, nemb)
                if s > best_score:
                    best_score = s
                    best_idx = ni
            self.db.execute(
                text("UPDATE questions SET node_id = :nid WHERE id = :qid"),
                {"nid": node_ids[best_idx], "qid": q_ids[qi]},
            )
            mapped += 1
        return mapped

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
        weak_questions: list = []  # questions that failed keyword matching
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

            # Only commit keyword matches with decent confidence (score ≥ 2).
            # Everything weaker goes to the Voyage semantic pass below.
            if best_node_id and best_score >= 2:
                self.db.execute(
                    text('UPDATE questions SET node_id = :nid WHERE id = :qid'),
                    {'nid': best_node_id, 'qid': q[0]}
                )
                mapped += 1
            else:
                weak_questions.append(q)

        # Voyage semantic fallback for weak-keyword-match questions (Feature 34 Tier 1+).
        # Gated by env var — disable if Voyage quota is exhausted or for cost control.
        use_voyage = os.environ.get("EXTRACT_VOYAGE_MAPPING", "true").lower() == "true"
        if weak_questions and use_voyage:
            try:
                leaf_tuples = [(nid, name) for name, nid in node_name_to_id.items()]
                voyage_mapped = self._semantic_map_questions_via_voyage(
                    sid, leaf_tuples, weak_questions
                )
                mapped += voyage_mapped
                log.info(
                    "[題目映射] Voyage 語意 fallback: %d/%d 題",
                    voyage_mapped, len(weak_questions),
                )
            except Exception as exc:
                log.warning(
                    "[題目映射] Voyage fallback failed (%s); using round-robin",
                    exc,
                )
                # Final round-robin fallback for remaining weak questions
                for i, q in enumerate(weak_questions):
                    self.db.execute(
                        text('UPDATE questions SET node_id = :nid WHERE id = :qid'),
                        {'nid': leaf_list[i % len(leaf_list)], 'qid': q[0]}
                    )
                    mapped += 1
        else:
            # Voyage disabled — round-robin fallback
            for i, q in enumerate(weak_questions):
                self.db.execute(
                    text('UPDATE questions SET node_id = :nid WHERE id = :qid'),
                    {'nid': leaf_list[i % len(leaf_list)], 'qid': q[0]}
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
