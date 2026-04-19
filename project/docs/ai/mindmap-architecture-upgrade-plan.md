# TiTi 心智圖架構升級計畫（2026 現代化對照 + 冷啟動問題處理）

**文件編號**: AI-mindmap-upgrade-plan
**產出角色**: CTO + AI/ML 工程師
**產出日期**: 2026-04-14
**狀態**: ✅ **Tier 1 + §3(E) + Tier 2 已完成於 2026-04-15**（Feature 34 BDD 24/24 通過，含 R1 補強）
**未實作項目（條件觸發）**:
- §3 Strategy B 考綱優先骨架（真實使用者回報冷啟動問題後再做）
- §3 Strategy F Dashboard 主動建議 UI（前端 Dashboard 改版時一併做）
- Tier 3 全部（Embedding 全量遷移、Incremental Mindmap、Gemini 3 切換）

**永久跳過項目（外部條件不滿足）**:
- Anthropic Admin API 整合（CertiMate 為個人帳號，Admin API 僅限 Team/Enterprise Organization；
  程式碼 `AnthropicUsageService` 已預備好，未來升級 Org 時設環境變數即可啟用）
**對應現有模組**:
- `backend/app/services/unified_knowledge_extraction_service.py`
- `backend/app/services/retrieval_service.py`
- `backend/app/services/embedding_service.py`
- `backend/app/services/reverse_engineering_service.py`
- `backend/app/models/syllabus_topic.py`

---

## §1 現況盤點（2026-04 真實狀態）

| 軸 | 現況 |
|----|------|
| **Embedding** | Voyage-3，1024 維純文字，HNSW 索引已建立 |
| **檢索** | 單階段 pgvector，`top_k=10`，**無 rerank** |
| **心智圖生成** | `unified_knowledge_extraction_service.extract()` → **單次 Gemini 2.5 Flash one-shot** → 整棵樹重寫 |
| **LLM** | `gemini-2.5-flash`（config.py 固定）|
| **刪除處理** | `chunk_repo.delete_by_resource_id` 硬刪 → 整科目重 extract |
| **Mastery 整合** | `node_mastery` + `schedule_service` 存在，但 `retrieval_service` **不過濾** |
| **Context Caching** | ❌ 未使用 |
| **考綱基礎設施** | ✅ `syllabus_topics` 表 + `reverse_engineering_service` 已實作（Feature 26）|

---

## §2 分級優化計畫（從 2026 現代化方案精準篩選）

完整 7 項對照分析已保留在 session 對話中。以下為**工程可行、風險可控的採用清單**：

### 🟢 Tier 1 — 立即執行（本週內完成）

| # | 項目 | 工期 | 收益 | 風險 |
|:-:|------|:---:|------|:---:|
| **T1-A** | **Mastery-aware Retrieval**：`retrieval_service.search()` 加 SQL WHERE 過濾已熟練 chunks | 4 小時 | 學習效率立即提升（聚焦弱點）| 極低 |
| **T1-B** | **Voyage Reranker-2.5 整合**：在 `retrieval_service` 加 stage 2，pgvector top 100 → rerank → top 5 | 1 天 | RAG 品質大幅提升，連帶考題品質提升 | 低（延遲 +500ms）|
| **T1-C** | **Gemini Context Caching**：考綱 + prompt 模板固定部分走 cache | 1 天 | 月省 $20-50 AI 成本 | 低（cache 失效時 fallback）|

### 🟡 Tier 2 — 中期（Q2 內完成）

| # | 項目 | 工期 | 觸發條件 |
|:-:|------|:---:|----------|
| T2-A | `knowledge_node_sources` 多對多表 + 軟刪剪枝 | 3 天 | 使用者回報「刪除資源後畫面跳動」 |
| T2-B | Gemini 2.5 Pro A/B 試跑 `unified_knowledge_extraction` | 1 天 | Tier 1 完成後 |
| T2-C | 考綱 JSON Schema 強制 6 chapter 輸出 | 半天 | 搭配 §3 骨架失焦處理一起做 |

### 🔴 Tier 3 — 未來路線圖（條件觸發）

| # | 項目 | 觸發條件 |
|:-:|------|----------|
| T3-A | Gemini Embedding 2 全量遷移 | 真實多模態需求（音訊/影片）出現 |
| T3-B | Incremental Mindmap Generation（Skeleton + Routing + 增量）| 單科目資源 > 50 份且使用者抱怨延遲 |
| T3-C | Gemini 3.x 切換 | Google 正式 GA |

### ❌ 不採用

- 全量 re-embed（成本過高，現有 Voyage-3 品質已足夠）
- 完全廢棄 `unified_knowledge_extraction_service`（400+ 行成熟閉環，不值得重寫）

---

## §3 冷啟動問題：骨架失焦與處理策略

### §3.1 問題描述

> 「若先生成骨架（6 個錨點），當使用者一開始只上傳 1-2 份資料時，是否會因資料量不足導致錨點失焦？」

**答：是的，這是真實問題。** 具體表現形式：

| 失焦模式 | 範例 |
|---------|------|
| **過度細分** | 1 份 PDF 被硬切成 6 個 chapter，每個 chapter 只對應 PDF 的一小段，語意重複 |
| **空洞 chapter** | 5 個 chapter 有內容、1 個完全空（使用者只上傳單一章節主題資料）|
| **錯位錨點** | AI 為了湊 6 個，虛構考綱外的章節名（例如把「附錄」升格為 chapter）|
| **不穩定跳動** | 使用者上傳第 2 份資料 → 骨架整個重建 → chapter 名字全變了 → 使用者學習進度感迷失 |
| **偏見放大** | 僅有的 1 份資料若偏向某個子主題，6 個 chapter 都會被染色到該方向 |

### §3.2 候選策略評估

| 策略 | 說明 | 優點 | 缺點 | CertiMate 可行性 |
|------|------|------|------|:---:|
| **A. 延遲生成** | 資料量未達門檻（如 3 份）不產骨架，顯示「請先上傳更多資料」| 品質保證 | 冷啟動零內容，UX 差 | 🟡 過度保守 |
| **B. 考綱優先** | 用**官方/逆向工程產出的考綱**當骨架，使用者資料只填充葉節點 | 穩定、權威、不受資料量影響 | 需有考綱資料 | ✅ **CertiMate 已有 `syllabus_topics` + Feature 26** |
| **C. 漸進骨架** | 1-2 份 → 3-4 chapter；5+ 份 → 完整 6 chapter | 適應資料量 | 數字跳動使用者困惑 | 🟡 數量浮動 |
| **D. 混合錨點** | 使用者資料覆蓋足時用使用者版本，否則 fallback 考綱 | 平衡權威 + 個人化 | 實作複雜 | 🟡 複雜 |
| **E. 置信度標示** | AI 為每個 chapter 輸出「支撐資料強度」，弱的標灰色「待補充」| 透明、可控 | 需 AI 自評 | ✅ 易整合 |
| **F. 建議型補充** | 生成後標「草稿」，主動建議使用者補充哪類資料 | 引導使用者行為 | 使用者可能不理會 | ✅ 易整合 |

### §3.3 🎯 推薦策略：**B + E + F 三重防護**

```
┌──────────────────────────────────────────────────────┐
│  層 1：考綱優先（Strategy B）                          │
│  ┌────────────────────────────────────────────────┐  │
│  │  骨架永遠從 syllabus_topics 產生               │  │
│  │  ├─ 有官方考綱 → 直接用                        │  │
│  │  └─ 無官方考綱 → reverse_engineering_service   │  │
│  │     從考古題反推（Feature 26 既有能力）        │  │
│  └────────────────────────────────────────────────┘  │
│                        ↓                              │
│  層 2：置信度標示（Strategy E）                        │
│  ┌────────────────────────────────────────────────┐  │
│  │  每個 chapter 計算「使用者資料覆蓋強度」      │  │
│  │  ├─ 強度 0 → 灰色「待補充」                   │  │
│  │  ├─ 強度 低 → 淺色 + 提示                     │  │
│  │  └─ 強度 高 → 正常色 + mastery 狀態           │  │
│  └────────────────────────────────────────────────┘  │
│                        ↓                              │
│  層 3：主動建議（Strategy F）                          │
│  ┌────────────────────────────────────────────────┐  │
│  │  Dashboard 顯示「{Chapter 名} 尚無資料，建議   │  │
│  │  上傳相關內容」含範例關鍵字                   │  │
│  │  可連結到資源上傳頁面預填搜尋                 │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### §3.4 三重策略的具體優勢

| 面向 | 效果 |
|------|------|
| **骨架永遠穩定** | 使用者上傳第 1/第 2/第 10 份資料時，6 個 chapter 不會跳動（因為骨架源自考綱而非資料）|
| **冷啟動有內容** | 使用者一上傳第 1 份資料就能看到完整骨架 + 該資料歸類到對應 chapter |
| **誠實顯示** | 空的 chapter 用灰色表達「尚未補充」，不裝作「已知」|
| **引導行為** | 明確告訴使用者補什麼資料 → 自我驅動上傳更多 → 平台黏著度提升 |
| **與考古題整合** | Feature 26 的 reverse engineering 成為「無官方考綱時的 fallback 資料來源」，已有設施最大化利用 |

### §3.5 支撐強度計算公式（供工程實作參考）

```python
def compute_chapter_strength(chapter_node, user_chunks):
    """
    回傳 0.0 - 1.0，代表該 chapter 被使用者資料覆蓋的程度。
    """
    chapter_keywords = set(chapter_node.keywords)  # 來自 syllabus_topic 或 AI 萃取

    # 1. 多少個使用者 chunks 與 chapter 關鍵字 overlap
    relevant_chunks = [
        c for c in user_chunks
        if len(chapter_keywords & set(c.keywords)) >= 2
    ]

    # 2. 向量距離檢查（較嚴格）
    chapter_embedding = embed_query(chapter_node.name + " " + " ".join(chapter_keywords))
    close_chunks = [
        c for c in relevant_chunks
        if cosine_sim(c.embedding, chapter_embedding) >= 0.75
    ]

    # 3. 計算強度
    if len(close_chunks) == 0:
        return 0.0
    if len(close_chunks) >= 5:
        return 1.0
    return len(close_chunks) / 5.0
```

**分級顯示**：
- `strength == 0` → 灰色 + 「待補充」標籤 + 補充建議
- `0 < strength < 0.3` → 淺色 + 「資料稀疏」警示
- `0.3 <= strength < 0.7` → 正常色 + 「建議多上傳類似資料」
- `strength >= 0.7` → 正常色 + 可開始練習 mastery

### §3.6 實作時對現有 service 的改動範圍

| 現有 service | 改動類型 | 影響 |
|------|------|------|
| `unified_knowledge_extraction_service.py` | **改寫 `_build_unified_prompt`**：輸入改為「syllabus_topics 樹 + user chunks」，要求 AI 把 user chunks 歸類到既有 chapter，而不是重建 chapter | 中等 |
| `reverse_engineering_service.py` | 新增「當科目無考綱時，第一次 extract 前自動觸發」的 hook | 小 |
| `knowledge_nav_service.py` | 查詢節點時加 `strength` 欄位到 API 回應 | 小 |
| 前端 `MindMapTree` 元件 | 依 `strength` 調整節點色彩 + 顯示「待補充」提示 | 中 |
| DB schema | 新增 `knowledge_nodes.support_strength` FLOAT 欄位 | 小（一個 migration）|
| Feature 03a 知識心智圖生成 | 新增 Scenarios：空 chapter 顯示、強度計算、補充建議 | 中 |

---

## §4 建議執行順序

```
Week 1: Tier 1 全部完成
  ├─ T1-A Mastery-aware Retrieval（半天）
  ├─ T1-B Voyage Reranker-2.5（1 天）
  └─ T1-C Gemini Context Caching（1 天）

Week 2-3: §3 骨架失焦處理（策略 B + E + F）
  ├─ Day 1: Migration 加 support_strength 欄位
  ├─ Day 2-3: 改 unified_knowledge_extraction_service 接 syllabus_topics
  ├─ Day 4: 前端 MindMapTree 加強度色彩
  ├─ Day 5: BDD 測試 + QA 驗收
  └─ Day 6-7: 主動建議 UI + 連結到資源上傳

Week 4: Tier 2
  ├─ T2-A 軟刪剪枝（可延後）
  ├─ T2-B Gemini 2.5 Pro A/B（1 天）
  └─ T2-C JSON Schema 強制 6 chapter（已在 §3 處理完畢）

Q2 後期: Tier 3 條件觸發
```

---

## §5 風險與降級路徑

| 風險 | 機率 | 對策 |
|------|:----:|------|
| Reranker API 延遲過高影響 UX | 🟡 中 | 設定 500ms timeout，fallback 回純 pgvector 結果 |
| Gemini Context Caching cache miss 頻繁 | 🟡 中 | 監控 cache hit rate，低於 60% 時自動停用 |
| 考綱不存在且考古題也不足時無法產生骨架 | 🔴 高 | fallback 到「請先上傳 3 份資料後再生成」的保守模式 |
| Reranker 成本超預算 | 🟡 中 | 整合到 Feature 33 AI_VOYAGE scope 的配額鎖，達門檻時降級為純 pgvector |
| 支撐強度計算耗時 | 🟡 中 | cache per-chapter 結果 5 分鐘，避免每次查詢重算 |

---

## §6 Feature 33 整合點

| 項目 | 對應 Feature 33 元件 |
|------|---------------------|
| Reranker 成本追蹤 | `ai_usage_ledger` provider=`voyage` feature=`rerank` |
| Voyage 配額鎖 | 既有 `VoyageQuotaService.check_and_reserve()`，reranker 成本加入預估 |
| Gemini Context Cache 成本 | `ai_usage_ledger` provider=`gemini` feature=`mindmap_cached` |
| Tier 2 Gemini Pro A/B | 用 `BudgetService.evaluate_alerts` 監控 Pro 模型燒錢速度 |

---

## §7 未來繼續執行的起點

下次要啟動時，只需告訴 CTO：「**執行 Tier 1**」或「**執行骨架失焦處理**」。本文件已記錄所有決策與推薦路徑，不必重新澄清。
