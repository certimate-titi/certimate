# Phase 1: 概念驗證與 MVP 開發詳解

## M1 (4月)：基礎架構建立與 AI 驗證

### 架構與 DevOps (基礎建設)
- **環境開通**：申請 GCP 專案，開通 Cloud Run、Cloud Storage、Cloud SQL (PostgreSQL)。
- **資料庫初始化**：建立 Cloud SQL for PostgreSQL，啟用 `pgvector` 擴充套件（向量語意搜尋）與 `pg tsvector`（全文精準關鍵字搜尋），設計基礎 Schema（Users、Resources、Flashcards、LearningSchedule、Subscriptions）。
- **CI/CD 建置**：建立 GitHub Repository，設定 GitHub Actions 自動打包 Docker Image 並推播至 Artifact Registry。
- **網域綁定**：設定 Cloudflare DNS 指向 Cloud Run 負載平衡器。

### AI 與提示詞工程 (AI Core)
- **OpenRouter 串接**：測試 `gemini-1.5-flash`（Free / Pro 基底）與 `claude-3.5-sonnet`（Pro Plus 高階任務）的模型切換穩定性。
- **Prompt 設計 - 知識點萃取**：穩定輸出 3-5 個高價值知識節點，並生成心智圖 JSON 結構（父子節點關聯）。
- **Prompt 設計 - 考題生成**：生成符合 JSON Schema 格式的題目、選項、正確答案與詳解。
- **KaTeX 渲染測試**：使用 Claude 3.5 Sonnet 測試手寫數學公式圖片（Pro Plus Vision OCR 路線）轉換，驗證 `$$...$$` 公式在前端的完整渲染。

## M2 (5月)：後端 Pipeline 與資料解析核心

### 核心 API 開發 (Main API)
- **會員系統**：實作基礎使用者登入，JWT Token 簽發與驗證機制。
- **資料庫 CRUD**：開發考題存取 API，支援儲存作答紀錄與學習排程更新。
- **事件驅動架構**：建置 GCP Pub/Sub Topic 與 Subscription，測試前端上傳後正確派發訊息至訊息佇列。

### AI 背景處理器 (Python AI Worker)
- **微服務建置**：以 FastAPI 建立 Worker，訂閱 Pub/Sub Topic。
- **PDF / TXT / Markdown 解析模組**：整合 `pdfplumber` 或 `Unstructured.io`，將講義自動解析成純文字後正規化為 `.md` 格式。
- **Vision OCR 管線（Pro Plus 限定）**：接收圖片 URL，呼叫 GPT-4o Vision 或 Claude 3.5 將手寫圖片精準轉換為 Markdown + KaTeX。在 Worker 端验证 `Subscription_Tier === PRO_PLUS` 方可觸發；低階方案呼叫立即返回 403。
- **雙軌儲存流程**：
  1. 解析成功 (COMPLETED)：寫入 GCS .md 檔（Layer 1）→ 切塊 Embedding 寫入 pgvector（Layer 2）→ 靜默刪除原始檔。
  2. 解析失敗 (FAILED)：保留原始檔於 GCS，等待使用者在資源庫觸發「重新解析」重試，成功後才刪除。
- **SSE 推播**：Worker 完成任務後，透過 Server-Sent Events 推播 COMPLETED / FAILED 狀態給前端。

### 擴充資源擷取 (MCP Server)
- **YouTube 解析器**：建立 `youtube-transcript-mcp-server`，處理 YouTube URL，下載逐字稿、清洗口語贅字並重建標點，回傳帶時間戳的結構化純文字。

## M3 (6月)：前端實作與內部 MVP 測試

### 前端開發 (Next.js)
- **UI 框架建置**：安裝 TailwindCSS 與 shadcn/ui 元件庫，建立基礎 Color Palette 與 Typography。
- **核心介面 - 上傳區**：
  - Tab A（檔案）：PDF / MD / TXT 全方案，Image（Vision OCR）**僅 Pro Plus 顯示，其他方案自動觸發 Paywall 彈窗**。
  - Tab B（YouTube URL）：所有方案皆可，Pro 以上無時長限制。
  - 解析狀態三段式回饋：進度條 (PENDING) → 綠色 Toast (COMPLETED) → 紅色重試按鈕 (FAILED)。
- **核心介面 - 測驗區**：引入 `react-markdown` 與 `rehype-katex`，確保數學題目以標準考卷格式渲染。
- **核心介面 - 資源庫**：實作 COMPLETED / FAILED 狀態標籤，FAILED 資源顯示重新解析按鈕；刪除 COMPLETED 資源前彈出連鎖清除防呆警告。

### 內部測試與整合 (Integration)
- **End-to-End 測試**：執行完整的「上傳文檔 → Queue → Worker 解析 → .md 寫入 GCS → pgvector 入庫 → 原始檔刪除 → SSE 通知 → 使用者作答 → 成績儲存」測試。
- **除蟲 (Bug Squash)**：修正資料整合格式、Timeout、以及 FAILED/COMPLETED 邊界條件下的異常行為。
