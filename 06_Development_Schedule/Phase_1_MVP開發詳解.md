# Phase 1: 概念驗證與 MVP 開發詳解

## M1 (4月)：基礎架構建立與 AI 驗證

### 架構與 DevOps (基礎建設)
- **環境開通**：申請 Google Cloud Platform 專案，開通 Cloud Run、Cloud Storage、Cloud SQL。
- **資料庫初始化**：建立 Cloud SQL for PostgreSQL，並配置 `pgvector` 擴充套件，進行基礎 Schema (Users, Exams, Subscriptions) 設計與建表。
- **CI/CD 建置**：建立 GitHub Repository，設定 GitHub Actions 實現前端 (Next.js) 與後端 API (Node.js/Go) 自動打包 Docker Image 並推播至 Artifact Registry。
- **網域綁定**：設定 Cloudflare DNS 指向 Cloud Run 負載平衡器。

### AI 與提示詞工程 (AI Core)
- **OpenRouter 串接**：註冊並測試 OpenRouter API，確保 `gemini-1.5-flash`、`claude-3.5-sonnet` 等模型能成功切換。
- **Prompt 設計 - 知識點萃取**：設計並測試擷取核心知識點的提示詞，目標是穩定輸出 3-5 個高價值概念。
- **Prompt 設計 - 單選題生成**：撰寫考題生成 Prompt，要求生成符合 JSON Schema 格式的題目、選項、正確答案與詳解。
- **KaTeX 渲染測試**：使用 Claude 3.5 Sonnet 測試包含複雜公式的圖片轉換，驗證生成的 Markdown 語源能在前端完美加載渲染 `$$...$$` 公式。

## M2 (5月)：後端 Pipeline 與資料解析核心

### 核心 API 開發 (Monolith Main API)
- **會員系統基礎**：實作基礎的使用者註冊/登入介面，JWT (或 Session) Token 簽發與驗證機制。
- **資料庫 CRUD**：開發考題存取 API (`GET /exams`, `POST /exams/submit`)，支援從前端儲存作答紀錄。
- **事件驅動架構 (Event-Driven)**：建置 GCP Pub/Sub Topic 與 Subscription，測試前端上傳檔案時能正確派發訊息至訊息佇列。

### AI 背景處理器 (Python AI Worker)
- **微服務建置**：以 FastAPI 或單純 Python 腳本建立 Worker，訂閱上述的 Pub/Sub Topic。
- **PDF/TXT 解析模組**：整合 `pdfplumber` 或 `Unstructured.io`，將講義自動解析成純文字。
- **Vision OCR 管線**：接收圖片 URL，呼叫 GPT-4o Vision 或 Claude 3.5 將圖片精準轉換為 Markdown。
- **文本切塊與向量化 (Chunking & Embedding)**：實作文字切片邏輯，將純文字轉換為 Embedding 向量並寫入 Cloud SQL (`pgvector`)。
- **長效任務推播**：整合 WebSocket (Socket.io) 或是 SSE，確保 Worker 完成任務後，可以通知前端。

### 擴充資源擷取 (MCP Server)
- **Youtube 解析器**：建立 `youtube-transcript-mcp-server`，處理 YouTube URL，下載逐字稿與時間軸。

## M3 (6月)：前端實作與內部 MVP 測試

### 前端開發 (Next.js)
- **UI 框架建置**：安裝 TailwindCSS 與 shadcn/ui 元件庫，並建立專案的基礎 Color Palette 與 Typography (響應式設計準備)。
- **核心介面 - 上傳區**：實作可彈性拖曳檔案與貼上 YouTube 網址的上傳介面，並串接前端直傳 GCS 機制。
- **核心介面 - 測驗區**：實作模擬考卷 UI，引入 `react-markdown` 與 `rehype-katex`，確保所有數學題目能以標準考卷格式渲染。
- **核心介面 - 錯題本**：實作使用者考後檢視對錯、查看詳細解析的畫面。

### 內部測試與整合 (Integration)
- **End-to-End (E2E) 測試**：執行完整的「上傳文檔 -> 跑完 Queue -> 生成題目 -> 使用者作答 -> 儲存紀錄」測試。
- **除百蟲 (Bug Squash)**：修正前後端資料整合格式、Timeout 議題、以及極端邊界條件 (Edge cases) 下的應用崩潰。
