---
name: preseed-mindmaps
description: 用本地端 Claude Code 當 LLM，批次預生科目預設心智圖（以考古題為素材），省下 Gemini/Anthropic API 費用。產出後寫回 DB 供使用者即時使用。
user-invocable: true
argument-hint: "[local|production] [subject_id?]"
input: target 環境 + optional subject_id（單科模式）
output: 每個 subject 的節點樹 JSON + DB 寫入報告 + 成本對比
---

# 角色

你是 CertiMate 的 **考古題心智圖預生成工程師**。負責把既有 `questions` + `historical_exams` 的內容分析成 `knowledge_nodes` 樹，**不呼叫任何外部 LLM API** — 改由當前 Claude Code session 本身作為 LLM 直接分析並產出結果。

**為什麼這樣做**：
- Gemini / Claude API 每個 subject 約 $0.02-5 USD，27 科批次 $0.5-140
- Claude Code 執行時 API 費用已由使用者訂閱 cover，增量成本 = 0
- 冷啟動場景（使用者選科目第一次看心智圖）可完全免 API call
- 生成的節點樹是靜態資料，一次寫入後反覆使用

---

# 工作流程

## Phase 1 — 蒐集輸入資料（Read only）

對每個目標 subject 執行：

```python
# 連 DB（local 用 5433, production 用 cloud-sql-proxy 5434）
# 取得考古題摘要
SELECT q.stem, q.options, q.answer_key, he.exam_name, he.year
FROM questions q
JOIN historical_exams he ON q.historical_exam_id = he.id
WHERE (he.exam_code || ':' || he.subject_code) IN (
    SELECT jsonb_array_elements_text(s.exam_subject_codes)
    FROM subjects s WHERE s.id = :sid
)
LIMIT 500
```

輸出到 `/tmp/preseed_input_{subject_slug}.json`：
```json
{
  "subject_id": "...",
  "subject_name": "證券商業務員",
  "question_count": 760,
  "questions": [
    {"stem": "...", "options": ["A", "B", "C", "D"], "answer": "A", "exam": "114年..."},
    ...
  ]
}
```

## Phase 2 — Claude Code 分析（本地 LLM，零 API 費用）

**必須對齊 `UnifiedKnowledgeExtractionService._build_unified_prompt()` 的輸出規格**，否則後端寫入、支撐強度計算、前端雷達圖會全錯位。現行規格 = **2 層知識樹 + 節點 meta（Bloom / exam_frequency）+ 關鍵字映射**。

### 2.1 萃取規則（直接對照後端 prompt）

1. **第一層：章（Chapter）** — 核心主題，**最多 6 個**（嚴禁超過 6，對應 Feature 13 雷達圖六軸）
2. **第二層：節（Section）** — 每章下 2-6 個知識點，每個節必須含：
   - `name`：繁體中文，簡潔明確
   - `description`：50-100 字說明
   - `exam_frequency`：`high` / `medium` / `low`（依考古題實際出現次數判斷）
   - `bloom_levels`：Bloom 認知層次陣列，值 ∈ `remember / understand / apply / analyze / evaluate / create`
3. **交叉比對**：考古題出現但教材沒提 → 仍列入；教材有但考古題沒考過 → 仍列入
4. **同一概念只建一個節點** — 語意相同就合併
5. **只用繁體中文**，不要猜測未出現的知識點

### 2.2 輸出 JSON 格式（必須 1:1 對齊）

```json
{
  "subject_id": "...",
  "subject_name": "證券商業務員",
  "knowledge_tree": {
    "chapters": [
      {
        "name": "證券市場基礎",
        "description": "章說明",
        "sections": [
          {
            "name": "初級市場與次級市場",
            "description": "介紹證券發行的承銷流程、次級市場的交易機制...",
            "exam_frequency": "high",
            "bloom_levels": ["remember", "understand"]
          }
        ]
      }
    ]
  },
  "question_keywords": {
    "初級市場與次級市場": ["初級市場", "次級市場", "承銷", "IPO"]
  }
}
```

**只回傳這個 JSON** — 給 Phase 3 的寫入腳本吃。

### 2.3 Bloom 層次判斷準則

- `remember`：需背誦定義、條文、數字 → 題幹含「下列何者為...」、「依法規定...」
- `understand`：概念比較、分類 → 題幹含「差異」、「特徵」、「屬於」
- `apply`：計算、套公式、情境題 → 題幹含「若...則」、「試計算」
- `analyze`：拆解、歸納 → 題幹含「原因」、「造成」、「影響因素」
- `evaluate`：評估優劣、判斷合適性 → 題幹含「下列何者最適當」、「評估」
- `create`：設計、規劃（考古題中罕見，多為申論題）

同一節可有多個 Bloom 層次。

## Phase 3 — 寫入 DB（交給後端既有 pipeline）

**不要自己寫 raw INSERT** — 直接複用 `UnifiedKnowledgeExtractionService._save_knowledge_tree()`。差異只在：跳過 `_call_gemini()`，改把 Phase 2 的 JSON 直接餵進去。

### 3.1 注入點（推薦做法）

寫一個 thin 腳本 `backend/app/scripts/preseed_mindmaps_from_local_llm.py`：

```python
from app.services.unified_knowledge_extraction_service import UnifiedKnowledgeExtractionService

def preseed(subject_id: str, llm_output_json_path: str):
    with open(llm_output_json_path) as f:
        result = json.load(f)  # Phase 2 產出
    
    svc = UnifiedKnowledgeExtractionService(db)
    
    # 複製 extract() 內部流程但跳過 AI call
    svc._clear_old_nodes(subject_id)
    tree = result["knowledge_tree"]
    question_keywords = result.get("question_keywords", {})
    nodes_created = svc._save_knowledge_tree(subject_id, tree, question_keywords)
    
    # 題目映射（依 question_keywords）
    svc._map_questions_to_nodes(subject_id, subject_name, question_keywords)
    
    # resource_chunks 映射（可能為空，但仍要跑以防有舊資源）
    svc._remap_chunks_to_nodes(subject_id, question_keywords)
    
    db.commit()
    
    # Feature 34 §3 — 重算 support_strength（4 階分層）
    from app.services.mindmap_strength_service import MindmapStrengthService
    MindmapStrengthService(db).recompute_for_subject(subject_id)
```

**為什麼這樣做**：
- `_save_knowledge_tree` 已經處理 depth 計算、parent_id 對應、sort_order、bloom_levels → source_text 注入
- 自己寫 raw INSERT 會漏掉 `node_source`、`support_strength` 計算、`available_questions` 回填
- `_map_questions_to_nodes` 負責把 `question_keywords` 拿去對 question.stem 做關鍵字比對並寫 `questions.node_id`

### 3.2 Feature 34 四階支撐強度（自動計算）

`MindmapStrengthService(db).recompute_for_subject(sid)` 會對每個節點算出 `support_strength` (0.0-1.0)，前端讀時透過 `strength_to_display()` 分成 **4 階**：

| 階 | 範圍 | 顯示 | 顏色 |
|---|---|---|---|
| 1 | 0.0 | **待補充**（empty）| 灰 |
| 2 | 0.0 < s ≤ 0.33 | **稀疏**（sparse）| 淺色 |
| 3 | 0.33 < s ≤ 0.66 | **一般**（normal）| 中色 |
| 4 | 0.66 < s ≤ 1.0 | **充足**（rich）| 深色 |

**本 skill 的注意事項**：
- 考古題預生場景下，因為沒有 `resource_chunks`，`support_strength` 的計算式（直接 chunks × 2 + semantic_count）會很低
- 解法：在 `MindmapStrengthService._compute_node_strength()` 額外把「對應到該節點的考古題數量」納入（例如 `n_questions / 10`），讓純考古題來源的節點也能有非零強度
- **若該 service 尚未納入考古題因子**，需先擴充再跑 Phase 3，否則所有預生節點會全部顯示「待補充」灰階

## Phase 4 — 驗證

```sql
-- 節點數
SELECT subject_id, count(*) FROM knowledge_nodes GROUP BY subject_id;
-- 題目映射覆蓋率
SELECT s.name, count(DISTINCT q.id) AS mapped, 
       (SELECT count(*) FROM questions q2 
        JOIN historical_exams he ON q2.historical_exam_id=he.id
        WHERE (he.exam_code||':'||he.subject_code) IN 
          (SELECT jsonb_array_elements_text(s.exam_subject_codes))) AS total
FROM subjects s 
LEFT JOIN knowledge_nodes kn ON kn.subject_id=s.id
LEFT JOIN questions q ON q.node_id=kn.id
GROUP BY s.id, s.name
HAVING count(*) > 0;
```

產出報告：
- 每個 subject 的 nodes_created、questions_mapped、support_strength 分布
- 總花費 = $0（本地 LLM）
- 對比 API 版估算：Gemini Flash ~$0.3 / Claude Sonnet ~$3-5

---

# 環境切換

## Local dev
```bash
./scripts/local-dev-up.sh   # 啟動 postgres:5433 + backend + frontend
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5433/certimate-api_dev"
```

## Production
```bash
cloud-sql-proxy certimate-titi:asia-east1:certimate-db --port 5434 &
DATABASE_URL="postgresql+psycopg://postgres:Certimate2024!@127.0.0.1:5434/certimate"
```

**預設先跑 local 驗證**，確認節點品質、題目映射正確後再切 production。

---

# 安全規則

1. **只對 `exam_subject_codes` 有內容的 subject 執行** — 目前 production 是 9/27
2. **重跑前先備份**：
   ```sql
   CREATE TABLE knowledge_nodes_backup_YYYYMMDD AS SELECT * FROM knowledge_nodes;
   ```
3. **清除舊節點規則**：只刪 `node_source='HISTORICAL_QA'` 的，**不要動** `node_source='RESOURCE_EXTRACTION'`（使用者上傳資源產生的節點）
4. **FK 處理**：刪節點前要 `UPDATE questions SET node_id=NULL` 處理 `questions.node_id` 非 CASCADE 的 FK
5. **Production 執行前必須**：
   - Local dev 驗證通過
   - 至少目視檢查 2 個 subject 的節點樹品質
   - 取得使用者明確 "可以上 production" 指令

---

# 成本對比範例（9 subjects, 2710 題）

| 方式 | API 費用 | 時間 | 備註 |
|---|---|---|---|
| Gemini 2.0 Flash | ~$0.3 USD | ~5-10 min | 需 GEMINI_API_KEY |
| Claude Sonnet | ~$3-5 USD | ~8-15 min | 需 ANTHROPIC_API_KEY |
| **Claude Code 本地 LLM** | **$0** | ~15-25 min | 當前 session 直接分析 |

Claude Code 模式節省 $0.3~5，長期 27 科擴展可省 $1~15。雖單次不多，但可避免 production cold path 的 LLM 依賴（reranker 壞掉時 fallback 穩定）。

---

# 已知限制

- Claude Code 單次 context 有限 — 對每個 subject 最多分析 500 題，超過要分批
- 生成的節點樹品質 vs Gemini 差異需人工抽檢（建議 local dev 階段先抽 2-3 科對照）
- 不適用持續更新場景（使用者上傳資源時仍走 `document_processing_service` → `UnifiedKnowledgeExtractionService` 的 API 路徑）
- `syllabus_topics` 表目前為空，本 skill 產出的節點 **沒有** `syllabus_topic_id` 對應（node_source 固定 `HISTORICAL_QA`）
