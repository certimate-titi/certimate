# Phase 2: 封閉測試與系統迭代詳解

## M4 (7月)：Closed Beta (100 位白老鼠測試)

### 測試招募與部署 (Launch & Operation)
- **Beta 版部署**：將 Next.js 前端與 API 後端正式對外發布於 Cloud Run 平台，並確定所有 HTTPS / 憑證皆設定正確。
- **白老鼠招募**：透過社群 (如 PTT、Dcard 軟體工程版/國考版) 徵求 100 位封測用戶。
- **成效追蹤**：導入 Google Analytics 或 Mixpanel 收集前端按鈕點擊與停留時間，了解「使用者都在哪裡流失 (Drop-off)」。

### 壓力測試與擴容 (Stress Test & Scaling)
- **大檔上傳壓力測試**：重點測試 100 人同時上傳超過 50MB 原文書或 10 小時 YouTube 影片時，Pub/Sub Queue 的排隊機制與 Worker 自動擴容 (Auto-Scaling) 狀況。
- **異常處理 (Error Handling)**：優化 Worker 發生 Timeout 或 Memory Out of Bounds 時的重試機制 (Dead Letter Queue)，確保每個任務「至少被處理一次」或明確返回錯誤報告。

## M5 (8月)：成效調優與成本控制

### 生成品質優化 (AI Hallucination Control)
- **RAG 檢索調優**：調整 Vector DB (pgvector) 的相似度門檻值。如果使用者詢問「非題庫內容」，系統需準確攔截並回覆：「*此問題超出目前題庫範圍...*」，防止非相關幻覺。
- **錯題教練精修**：優化蘇格拉底教學法 Prompt，確保 AI 不直接給答案，而是點出「盲點」與「回溯原文 (Citation)」。

### 成本節流系統實作 (Cost Reduction)
- **快取架構 (Redis Cache)**：部署 Cloud Memorystore (Redis)。
- **Doc Hash 命中機制**：當使用者上傳檔案時，系統先產生檔案的 MD5 Hash 值，在 Redis 中查詢是否已有另一名用戶上傳過同一份講義或相同 YouTube 連結。若命中 (Cache Hit)，直接從 DB 複製一份測驗即可，達到 100% LLM 成本節省。

## M6 (9月)：準備 Public Beta (金流與權限)

### 會員授權與角色管理 (Auth & Authz)
- **Firebase Auth 導入**：捨棄自建 JWT，全面導入 Firebase Authentication 處理註冊、密碼重置與 Google OAuth 一鍵登入。
- **雙軌權限控制**：在資料庫 User Table 增加 `Subscription_Tier` 欄位 (Free / Pro)。
- **權限中介層 (Middleware)**：在 API Gateway 實作 Role-Based Access Control (RBAC)，Free 用戶將無權存取 `/exams/pro-features` 等進階端點。

### 金流與訂閱系統 (Subscription & Payment)
- **Stripe / 綠界 串接**：選擇並串接第三方支付平台，建立 $199 TWD/月的「定期定額」訂閱商品。
- **Webhook 處理機制**：實作一個用以接收 Stripe/綠界 Webhook 的 API，確保當信用卡扣款成功後，系統能自動把該用戶的 `Subscription_Tier` 改為 `Pro`。
- **訂閱管理介面**：實作前端「升級 Pro 版」、「取消訂閱」等帳務管理頁面。
