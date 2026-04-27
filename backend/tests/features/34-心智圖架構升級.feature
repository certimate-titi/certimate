@backend @mindmap_upgrade
Feature: 心智圖架構升級（Tier 1 + §3 + Tier 2）

  對應 `project/docs/ai/mindmap-architecture-upgrade-plan.md` 的實作驗證。
  這個 feature 集中驗證本次升級引入的新行為：
  - T1-A: Mastery-aware Retrieval（已熟練節點的 chunks 被排除於 RAG 之外）
  - T1-B: Voyage Reranker 兩階段檢索(含 graceful degrade)
  - T1-C: Gemini Context Caching stats tracking
  - §3 : support_strength 計算、Strategy E 顯示層
  - T2-A: resource_chunks 軟刪
  - T2-C: JSON Schema 強制 6 chapter（單元測試形式）

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                 | 訂閱方案    | 角色         |
      | 1        | super@certimate.com   | ULTRA_1599 | super_admin  |
      | 2        | learner@certimate.com | PRO_199    | user         |

  # ========== T1-A Mastery-aware Retrieval ==========

  Rule: 前置 - 檢索時應自動排除已熟練節點關聯的 chunks

    Example: 掌握節點的 chunks 被排除於 search_similar 之外
      Given 系統有一個科目 "AWS SAA" 含 2 個知識節點 "VPC"、"EC2"
      And 每個節點各關聯 3 個 resource_chunks
      And 使用者 "learner@certimate.com" 對 "VPC" 節點已標記為 "MASTERED"
      When 系統以使用者身份查詢與 "雲端網路" 相關的 chunks
      Then 檢索結果不應包含 "VPC" 節點的 chunks
      And 檢索結果應包含 "EC2" 節點的 chunks

    Example: 新使用者沒有任何 mastery 紀錄時返回所有 chunks
      Given 系統有一個科目 "AWS SAA" 含 1 個知識節點 "S3"
      And 該節點關聯 3 個 resource_chunks
      And 使用者 "learner@certimate.com" 尚未有任何 mastery 紀錄
      When 系統以使用者身份查詢與 "物件儲存" 相關的 chunks
      Then 檢索結果應包含所有 "S3" 節點的 chunks

  # ========== §3 Strategy E: support_strength 顯示層 ==========

  Rule: 後置（狀態）- 新節點的 support_strength 預設應為 0.0 (尚未測量)

    Example: 剛建立的節點預設強度為 0.0
      Given 系統建立一個新知識節點 "容器化"
      Then 該節點的 support_strength 應為 0.0

  Rule: 後置（計算）- MindmapStrengthService 應依使用者 chunks 覆蓋度計算強度

    Example: 節點有 5 筆以上直接關聯 chunks 時強度飽和為 1.0
      Given 系統有一個知識節點 "Docker 基礎" 關聯 5 個 resource_chunks
      When 系統呼叫 MindmapStrengthService.recompute_for_node("Docker 基礎")
      Then 該節點的 support_strength 應為 1.0

    Example: 節點無關聯 chunks 時強度為 0.0 (待補充狀態)
      Given 系統有一個知識節點 "Kubernetes" 無任何 resource_chunks
      When 系統呼叫 MindmapStrengthService.recompute_for_node("Kubernetes")
      Then 該節點的 support_strength 應為 0.0

  Rule: 後置（顯示）- strength_to_display 應對應四個 tier

    Example: 強度 0 對應 empty tier (待補充)
      When 系統計算 strength_to_display(0.0)
      Then 回應的 tier 應為 "empty"
      And 回應的 needs_supplement 應為 true

    Example: 強度 0.5 對應 partial tier (可補充更多)
      When 系統計算 strength_to_display(0.5)
      Then 回應的 tier 應為 "partial"

    Example: 強度 0.9 對應 full tier (資料充足)
      When 系統計算 strength_to_display(0.9)
      Then 回應的 tier 應為 "full"
      And 回應的 needs_supplement 應為 false

  # ========== T2-A 軟刪剪枝 ==========

  Rule: 後置（軟刪）- delete_by_resource_id 預設應執行軟刪

    Example: 軟刪後的 chunks 不再出現於檢索結果
      Given 系統有一個資源 "舊教材.pdf" 且已建立 3 個 chunks
      When 系統呼叫 delete_by_resource_id 不帶 hard 參數
      Then 該資源的 chunks is_deleted 欄位應為 true
      And 檢索結果不應再返回這些 chunks

    Example: 使用 hard=true 時執行實際 DELETE
      Given 系統有一個資源 "重建教材.pdf" 且已建立 2 個 chunks
      When 系統呼叫 delete_by_resource_id 並帶 hard=true
      Then 該資源的 chunks 應從 resource_chunks 表中物理刪除

  # ========== T1-C Gemini Context Caching ==========

  Rule: 後置（統計）- GeminiCacheService 應追蹤 hit/miss 統計

    Example: 首次查詢小型 prompt 時 cache miss
      Given GeminiCacheService 已初始化且無任何 entries
      When 系統以 100 字的 system_prompt 呼叫 get_or_create_cache
      Then 回應應為 None (prompt 太短不建立 cache)
      And stats.misses 應為 1

    Example: 可透過環境變數停用顯式快取
      Given 環境變數 GEMINI_EXPLICIT_CACHE_ENABLED 設為 "false"
      When 系統呼叫 GeminiCacheService.is_enabled()
      Then 回應應為 false

  # ========== T1-B Voyage Reranker 兩階段檢索 ==========

  Rule: 前置 - 啟用 Reranker 時應拉 100 個候選再精排到 top_k

    Example: 候選池小於 top_k 時不觸發 rerank
      Given RetrievalService 已啟用 rerank
      And 候選池只有 3 個 chunks
      When 系統請求 top_k=5 的檢索
      Then 系統不應呼叫 Voyage rerank API
      And 應返回全部 3 個候選

    Example: Voyage 配額達到 degrade 時 rerank fallback 至純 pgvector
      Given RetrievalService 已啟用 rerank
      And 候選池有 10 個 chunks
      And Voyage AI 當月用量達 degrade 門檻
      When 系統請求 top_k=3 的檢索
      Then rerank 應被跳過
      And 應返回 pgvector 前 3 個候選

    Example: Rerank API 失敗時靜默 fallback
      Given RetrievalService 已啟用 rerank
      And 候選池有 10 個 chunks
      And Voyage rerank API 會拋出例外
      When 系統請求 top_k=3 的檢索
      Then 應返回 pgvector 前 3 個候選
      And 系統應記錄 warning log

  # ========== T2-B Gemini Pro A/B env var ==========

  Rule: 前置 - GEMINI_UNIFIED_EXTRACTION_MODEL 環境變數應可動態切換模型

    Example: 預設環境變數使用 gemini-2.5-flash
      Given 環境變數 GEMINI_UNIFIED_EXTRACTION_MODEL 未設定
      When 系統重新載入 unified_knowledge_extraction_service 模組
      Then 模組層級的 GEMINI_MODEL 應為 "gemini-2.5-flash"

    Example: 設定 pro 模型時應切換為 gemini-2.5-pro
      Given 環境變數 GEMINI_UNIFIED_EXTRACTION_MODEL 設為 "gemini-2.5-pro"
      When 系統重新載入 unified_knowledge_extraction_service 模組
      Then 模組層級的 GEMINI_MODEL 應為 "gemini-2.5-pro"

  # ========== T2-C JSON Schema 強制 6 chapter ==========

  Rule: 後置 - response_schema 應限制 chapters 最多 6 個

    Example: response_schema 包含 maxItems=6 約束
      When 系統檢視 unified_knowledge_extraction._call_gemini 的 response_schema
      Then response_schema.properties.knowledge_tree.properties.chapters.maxItems 應為 6

    Example: schema 被拒絕時應 fallback 到無 schema 呼叫
      Given Gemini 回傳 schema 格式錯誤
      When 系統呼叫 _call_gemini
      Then 系統應 retry 一次不帶 response_schema
      And 應記錄 warning log "response_schema rejected"

  # ========== §3 強度邊界值 ==========

  Rule: 後置 - strength_to_display 應在邊界正確分級

    Example: 強度 0.3 邊界應為 partial
      When 系統計算 strength_to_display(0.3)
      Then 回應的 tier 應為 "partial"

    Example: 強度 0.299 應為 sparse
      When 系統計算 strength_to_display(0.299)
      Then 回應的 tier 應為 "sparse"

    Example: 強度 0.7 邊界應為 full
      When 系統計算 strength_to_display(0.7)
      Then 回應的 tier 應為 "full"

    Example: 強度 0.699 應為 partial
      When 系統計算 strength_to_display(0.699)
      Then 回應的 tier 應為 "partial"

    Example: 強度 1.0 應為 full
      When 系統計算 strength_to_display(1.0)
      Then 回應的 tier 應為 "full"

  # ========== §3 Strategy E Root Solution: Syllabus Anchors ==========

  Rule: 前置 - 有 syllabus_topics 時 extract() 的 6 章必須對齊錨點

    Example: extract 產出的章名應與 syllabus_topics 一致
      Given 系統有一個科目 "資訊安全" 含 6 個 syllabus_topics 章節
      And 該科目有 50 題考古題
      When 系統對 "資訊安全" 執行 UnifiedKnowledgeExtractionService.extract()
      Then 產出的第一層知識節點數量應為 6
      And 每個第一層節點名稱應與 syllabus_topics 章節名稱語意相近

  Rule: 後置（計算）- Layer 3 question_count 應讓純考古題科目非零強度

    Example: 節點有 10+ 映射考古題時強度飽和為 1.0
      Given 系統有一個知識節點 "密碼學基礎" 映射 12 題考古題且無 resource_chunks
      When 系統呼叫 MindmapStrengthService.recompute_for_node("密碼學基礎")
      Then 該節點的 support_strength 應為 1.0

    Example: 節點有少量映射考古題時強度介於 0-1
      Given 系統有一個知識節點 "網路安全" 映射 3 題考古題且無 resource_chunks
      When 系統呼叫 MindmapStrengthService.recompute_for_node("網路安全")
      Then 該節點的 support_strength 應大於 0.0 且小於 1.0

  Rule: 後置（聚合）- 章層級 strength 應繼承子節的平均值

    Example: 章包含 3 個子節各 strength 0.4 時章 strength 為 0.4
      Given 系統有一個章節點 "資訊安全治理" 包含 3 個子節點各 strength 0.4
      When 系統呼叫 MindmapStrengthService.recompute_for_subject
      Then "資訊安全治理" 的 support_strength 應約為 0.4

    Example: 章包含混合強度子節時取平均
      Given 系統有一個章節點 "網路與系統安全" 包含子節點 strength 分別為 1.0, 0.5, 0.0
      When 系統呼叫 MindmapStrengthService.recompute_for_subject
      Then "網路與系統安全" 的 support_strength 應約為 0.5

  Rule: 前置 - Voyage 語意映射應用於 keyword 匹配弱的考古題

    Example: keyword 弱匹配的題目走 Voyage 語意 fallback
      Given 系統有一個科目含 20 題考古題和 4 個知識節點
      And 其中 5 題的題幹不包含任何節點關鍵字
      When 系統對該科目執行 extract() 含 Voyage 語意映射
      Then 全部 20 題應被映射到某個知識節點
      And Voyage 語意 fallback 應至少處理 5 題

  Rule: 後置（品質 gate）- QA gate 應在每次 extract 自動檢查

    Example: extract 完成後 QA gate 應回報結果
      Given 系統對某科目執行 extract()
      Then 回傳結果應包含 qa_report 欄位
      And qa_report.failure_count 應為 0
      And qa_report.passed 應為 true
