# Phase 2: 封閉測試與系統迭代詳解

## M4 (7月)：Closed Beta (100 位封測)

### 測試招募與部署 (Launch & Operation)
- **Beta 版部署**：將 Next.js 前端與 API 後端正式對外發布於 Cloud Run，確認所有 HTTPS / 憑證皆設定正確。
- **封測招募**：透過社群 (PTT、Dcard 軟體工程版/國考版) 徵求 100 位封測用戶。
- **成效追蹤**：導入 Google Analytics / Mixpanel 收集前端點擊與停留時間，找出使用者流失 (Drop-off) 環節。

### 壓力測試與擴容 (Stress Test & Scaling)
- **大檔上傳壓力測試**：測試 100 人同時上傳 50MB PDF 或 10 小時 YouTube 影片時，Pub/Sub Queue 排隊機制與 Worker 自動擴容 (Auto-Scaling) 表現。
- **FAILED 重試穩健性測試**：驗證解析失敗時，原始檔確實保留於 GCS，重試後 COMPLETED 觸發正確刪除且不發生殘留檔案。
- **異常處理 (Error Handling)**：優化 Worker Timeout / Memory Out of Bounds 時的重試機制 (Dead Letter Queue)，確保每個任務「至少被處理一次」或明確返回錯誤報告。

## M5 (8月)：成效調優與成本控制

### 生成品質優化 (AI Hallucination Control)
- **RAG 檢索調優**：調整 pgvector 的相似度門檻值。問題超出題庫範圍時，精準攔截並回覆固定字串，防止幻覺且不觸發 LLM 計費。
- **AI 教練精修（Pro Plus）**：優化 Claude 3.5 蘇格拉底教學法 Prompt，確保 AI 點出「盲點」與「回溯原文 (Citation)」而非直接給答案。

### 成本節流實作 (Cost Reduction)
- **快取架構 (Redis Cache)**：部署 Cloud Memorystore (Redis)。
- **Doc Hash 命中機制**：上傳時先產生 MD5 Hash，在 Redis 查詢是否已有人上傳同一份內容。Cache Hit 時從 DB 直接複製，100% 節省 LLM 費用。
- **Claude 配額守門員**：Pro Plus 每月 200 次 Claude 教練額度由 Redis 原子計數器追蹤；Ultra 無上限但仍計費，須確保超額保護機制到位。

## M6 (9月)：準備 Public Beta（金流與三階層權限）

### 會員授權與角色管理 (Auth & Authz)
- **Firebase Auth 導入**：全面導入 Firebase Authentication 處理註冊、密碼重置與 Google OAuth 一鍵登入。
- **四軌權限控制**：在 User Table 增加 `Subscription_Tier` 欄位（FREE / PRO / PRO_PLUS / ULTRA），並在 API Gateway 實作 RBAC Middleware，嚴格管控各層端點的存取權限。

### 金流與訂閱系統 (Subscription & Payment)
- **Stripe / 綠界 串接**：建立三種定期定額訂閱商品：
  - **Pro**：199 TWD / 月（高速 AI 出題，無 Vision OCR 與 Claude 教練）
  - **Pro Plus**：399 TWD / 月（解鎖 Vision OCR、每月 200 次 Claude 高階教練）
  - **Ultra**：1599 TWD / 月（無限功能 + B2B 機構後台）
- **Webhook 處理機制**：實作 Stripe/綠界 Webhook 接收 API，扣款成功後自動更新 `Subscription_Tier`，並按方案即時配發對應配額。
- **訂閱管理介面**：實作「升級方案」、「降級（下期生效）」、「取消訂閱」等帳務管理頁面，並顯示 Pro Plus Claude 教練剩餘次數。
