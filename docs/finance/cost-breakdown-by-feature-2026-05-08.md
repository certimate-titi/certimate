# 功能花費佔比拆解 — 2026-05-08

> **目的**：CEO 線議題 B1 的延伸 — **每個功能各花多少錢**？這是定價、刪功能、cap 設定的真正依據。
> **方法**：在 `ai_usage_ledger` 既有 `feature` 欄位上，補齊所有 callsite 標籤 + 加 admin endpoint 即時查 → 兩週後拿真實佔比，不再靠粗估。

## 1. 雲端當前實況（2026-05-08）

從 `/api/v1/admin/cost/summary` 即時抓：

| Scope | 本月已用 (USD) | 上限 (USD) | 佔比 |
|-------|--------------:|----------:|-----:|
| AI_ANTHROPIC | 0.00 | 700 | 0% |
| AI_GEMINI | 0.01 | 100 | 0% |
| AI_VOYAGE | 0.05 | 50 | 0.09% |
| GCP_TOTAL（Cloud Run / GCS / Cloud SQL）| 18.98 | 400 | 4.74% |
| **合計** | **~19.04** | 1,250 | 1.5% |

**真實意義**：
- LLM 部分 < $0.06（admin 帳號測試級流量）
- **GCP infra 占 99.7%**（Cloud Run idle / Cloud SQL min instance）
- 所有 worst-case 預警值都用不上，因為 **沒幾個用戶在用**

## 2. 結構性問題：feature 標籤缺失

### 修正前（Sprint 8 T70 之前）

`ai_usage_ledger.feature` 只有 4 個明確標籤 + 1 個 generic：

| feature | 來源 service | 涵蓋業務 |
|---------|-------------|----------|
| `unified_extract` | unified_knowledge_extraction_service | Gemini 抽知識節點 |
| `unified_extract_map` | 同上 | Voyage 映射節點 |
| `document_embedding` | document_processing_service | Voyage chunk embedding |
| `rerank` | retrieval_service | Voyage 語意搜尋 rerank |
| `llm_generate` | **15+ 處 generic** | 完全混在一起，無法拆解 |

→ 一旦 LLM 用量起來，80%+ 都會落在 `(unlabeled)` / `llm_generate`，毛利分析失效。

### 修正後（Sprint 8 T70）

補上 12 個明確 feature 標籤，覆蓋所有 LLM callsite：

| feature | service | 對應業務功能 | Plan tier |
|---------|---------|--------------|:---------:|
| `ai_coach_chat` | knowledge_nav_service | AI 教練對話（PRO_PLUS+ 限定） | PP/U |
| `ai_question_gen` | ai_generation_service | AI 自動出題 | All |
| `ai_question_gen_fallback` | 同上 | JSON parse fail 後重試 | All |
| `exam_points_extract` | 同上 | 出題前抽考點 | All |
| `question_validate` | exam_bank/question_validator | 題目品質驗證 | (內部) |
| `exam_result_summary` | exam_result_service | 結算 AI 講評（FREE 不給） | PRO+ |
| `wrong_answer_explain` | wrong_answer_service | 錯題詳解 | All |
| `wrong_answer_classify` | 同上 | 錯題分類 16 token | All |
| `wrong_answer_advanced` | 同上 | 進階錯題分析 | PP/U |
| `encouragement` | encouragement_service | 鼓勵語 256 token | All |
| `weekly_report` | weekly_report_service | 週報 AI 摘要 512 token | All（被動寄送） |
| `knowledge_merge` | knowledge_merge_service | 節點合併判定 | (內部) |
| `doc_structure_md` | document_processing_service | 文件結構 markdown 化 | (上傳流程) |
| `doc_chapter_extract` | 同上 | 章節抽取 | (上傳流程) |
| `doc_subtitle_gen` | 同上 | 子標題生成 | (上傳流程) |
| `doc_structure_analysis` | 同上 | 整體結構分析 8000 token | (上傳流程) |
| `rag_with_context` | llm_service.generate_with_context | RAG 流程通用入口 | All |
| `json_generate` | llm_service.generate_json | JSON 結構化輸出通用入口 | All |
| `llm_generate` | llm_service 預設 | 未明確指定的剩餘 | (應為 0) |

## 3. 預估佔比（用戶量起飛後的「應然」分布）

基於：每用戶每月平均使用 30 次 chat、上傳 5 份文件、做 10 次測驗、看 3 次週報。

### B2C FREE 用戶（10 chat 上限）— per user per month

| feature | 預估 LLM 成本 (USD) | 佔比 |
|---------|------------------:|-----:|
| ai_coach_chat | 0.00 | 0%（FREE 無此功能）|
| ai_question_gen + exam_points_extract | 0.18 | 33% |
| exam_result_summary | 0.00 | 0%（FREE 無此功能）|
| wrong_answer_explain × 3 | 0.06 | 11% |
| encouragement × 5 | 0.01 | 2% |
| weekly_report × 4 | 0.04 | 7% |
| doc_*（上傳 5 份）| 0.20 | 36% |
| unified_extract + map（上傳 5 份）| 0.07 | 13% |
| document_embedding | 0.005 | 1% |
| rerank | 0.001 | 0% |
| **合計** | **~0.55** | 100% |

→ 折合 NTD ~17.6/月。FREE tier 售價 0、廣告補貼門檻清晰。

### B2C PRO_199 用戶（30 chat/天 + 50 upload + 100 exam）

| feature | 預估 LLM 成本 (USD) | 佔比 |
|---------|------------------:|-----:|
| ai_question_gen + exam_points_extract | 1.80 | 51% |
| exam_result_summary | 0.30 | 8% |
| wrong_answer_explain × 30 | 0.60 | 17% |
| encouragement | 0.10 | 3% |
| weekly_report | 0.04 | 1% |
| doc_*（50 份）| 0.45 | 13% |
| unified_extract + map | 0.18 | 5% |
| document_embedding | 0.05 | 1% |
| rerank（搜索）| 0.02 | 1% |
| **合計** | **~3.54** | 100% |

→ 折合 NTD ~113/月。**售價 NTD 199，毛利率 43%**（比 finance-analyst 估的 33% 略高，因為粗估包含 worst-case 配額燒滿）。

### B2C PRO_PLUS_399 用戶（200 chat + 200 upload + 500 exam + advanced_coach + vision 50 頁）

| feature | 預估 LLM 成本 (USD) | 佔比 |
|---------|------------------:|-----:|
| **ai_coach_chat × 50（PRO_PLUS 限定）** | 5.00 | **49%** 🚨 |
| ai_question_gen | 7.20 | 70% (前) → 30% (合計後) |
| wrong_answer_advanced × 30 | 1.20 | 12% |
| doc_structure_analysis（vision 解析）× 50 | 1.50 | 15% |
| 其他 | 1.40 | 14% |
| **合計** | **~16.30** | 100% |

→ 折合 NTD ~522/月。**售價 NTD 399，毛利率 -31%**（負毛利）。

**最大兇手**：
1. `ai_coach_chat` 用 advanced 模型，單次 ~ $0.10，50 次/月就 $5。
2. vision 50 頁 × $0.03 = $1.50（單頁解析比 chat 還貴）。

### ULTRA_1599 用戶（unlimited）

worst-case 用戶月成本：~$45 / NTD 1,440，毛利率 10%。但「unlimited」實際很少全燒，典型用量 ~$8 → 毛利率 80%（健康）。**致命風險**：1 個 abuse 用戶單月 $200+ token 燒掉 10 個正常 ULTRA 訂閱毛利。

## 4. 行動建議

### 立即（本 sprint）— 已實作

- ✅ T69 `GET /admin/cost/by-feature?days=30` admin endpoint，超管可隨時拉佔比
- ✅ T70 補齊 18 個 feature 標籤，覆蓋所有 LLM callsite（PR #16 後續 commit）

### 兩週內（資料累積後）

- 跑兩週數據，比對「預估佔比」vs「實際佔比」
- 重點看：
  - `ai_coach_chat` 是否真的吃掉 PRO_PLUS 50% 預算？→ 是 → 強化 cap / context window 截短
  - `doc_structure_analysis` 8000 token 是否每份必跑？→ 看 vision 用量分布
  - `(unlabeled)` / `llm_generate` 是否歸零？→ 驗證 T70 覆蓋完整

### 一個月內（決策點）

依實際數據決定：
- PRO_PLUS_399 漲價 vs 砍 ai_coach_chat 配額（200 → 100/天）
- ULTRA fair-use cap 落地（chat 400/天、upload 500/月）
- vision 解析改用 cheaper 模型（如 Gemini Flash 取代 Pro）

## 5. 與 議題 B1 / B2 的關係

| 議題 | 本文補強 |
|------|----------|
| B1 毛利儀表板 | 把「per-plan cost_usd」拆成「per-feature × per-plan」二維表，UI 多一個下拉切換 |
| B2 ULTRA fair-use cap | 從本文 `ai_coach_chat` 實際佔比決定 cap 數值（避免拍腦袋）|
| A 訂閱配額調整 | 用 `(feature, plan)` 二維資料看「哪個 plan 哪個功能用最兇」→ 動配額而非動價 |

---

**owner**：財務 + CTO（共同）  
**下次更新**：2026-05-22（兩週後拉真實 14 天數據）
