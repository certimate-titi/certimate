# AI 工作流設計

## 1. 資源解析與 RAG 流程
為了應對多模態的資源輸入 (文字、圖片、影片)，我們設計了三軌並行的資源萃取工作流，確保後續的 RAG (檢索增強生成) 擁有最高品質的文本基礎。

### 三軌解析步驟：
1. **文檔解析 (PDF/TXT/MD)**：利用 `pdfplumber` 或 `Unstructured.io` 進行常規文字萃取與排版還原。
2. **影音解析 (YouTube via MCP)**：呼叫背景的 `youtube-transcript-mcp-server`，直接取回帶有時間軸 (Timestamps) 的乾淨逐字稿。
3. **視覺解析 (Vision OCR for Math)**：若文件含有照片、手寫方程式，則繞過常規文字解析，直接呼叫 GPT-4o Vision 或 Claude 3.5 進入「**數學 OCR 管線**」，強制要求模型以 Markdown + KaTeX (`$$...$$`) 輸出排版完美的文本。

### 統一資料處理：
4. **切塊 (Chunking)**：將萃取出的純文字依據段落標題或固定 Token 數切片 (例如 500-1000 tokens)。若為 YouTube，則依據時間軸段落切塊。
5. **向量化 (Embedding)**：透過 OpenRouter 呼叫低成本、高效率的 Embedding 模型 (如 `text-embedding-3-small` 或開源的 `nomic-embed-text`) 將文本轉為向量，存入 Vector DB。

## 2. 考題生成工作流 (Exam Generation Pipeline)
參考既有技能 (`.agents\skills\generate_exam\SKILL.md`)：
1. **知識點提取**：從 Vector DB 撈回演算法指定的該複習區塊後，要求 LLM 總結 3-5 個核心知識點。
2. **動態模型路由 (OpenRouter)**：
   - **Free 版用戶 / 基礎單選題**：自動路由至 Token 成本極低的 `gemini-1.5-flash` 或 `llama-3-8b`。
   - **Pro 版用戶 / 複雜情境題與數學題**：自動路由至高階的 `claude-3.5-sonnet` 或 `gpt-4o` 確保邏輯與 LaTeX 語法完全正確。
3. **題綱設計**：根據知識點配置難易度 (易、中、難) 與題型 (單選、複選、填空、數學計算)。
4. **生成與格式化**：
   - Prompt 規範必須輸出為標準 JSON 格式以便程式 (Frontend) 直接反序列化渲染。
   - 必須包含溯源欄位：`question`, `options`, `correct_answer`, `explanation_markdown`, **`citation_chunk_id` (原文出處)**。
5. **驗證階段**：二次檢查 (Self-Consistency) 確保題目沒有邏輯錯誤且只有一個正確選項。

## 3. 錯題訂正與深度解析工作流 (Review & Feedback Pipeline)
參考既有技能 (`.agents\skills\review_exam\SKILL.md`)：
1. 收集使用者的答錯題目與原選項。
2. **智能教練分級分發**：
   - 若為 Free 版用戶：提供一句話的基礎正解提示 (`gemini-1.5-flash`)，並顯示解鎖 Pro 版對話的按鈕 (轉換漏斗)。
   - 若為 Pro 版用戶：啟動「知識引導教練」Prompt (`claude-3.5-sonnet`)，進行蘇格拉底式的循循善誘。
3. 輸出設計 (Pro 版專屬)：
   - **盲點痛擊**：精準點出為何使用者選的誘答選項是錯的。
   - **原文溯源 (Citation)**：明確指出這題考點出自於上傳講義的「哪一頁、哪一段」或 YouTube 影片的「哪一分哪一秒」。
   - **觀念重塑與記憶掛鉤**：提供記憶口訣或關聯對照表。

## 4. AI 問答防護機制 (Q&A Guardrails)
為了確保 AI 教練的回覆品質與控制 Token 成本，系統對問答功能設置以下防護規則：

### A. 回答範圍限定 (Scope Restriction)
- AI 教練的回答範圍**嚴格限定於使用者已上傳的題庫 / RAG 知識庫內的內容**。
- 系統在每次回覆前，先對使用者提問進行 RAG 檢索比對。若檢索結果的相似度分數低於門檻值 (Relevance Threshold)，判定為「非題庫內容」。
- 非題庫提問（如閒聊、超出範圍的問題）不觸發 LLM 生成，改為回覆固定引導訊息：「*此問題超出目前題庫範圍，請上傳相關學習資源後再試。*」

### B. 頻率管控與冷卻機制 (Rate Limiting & Cooldown)
- 若同一使用者在短時間內連續多次觸發「非題庫內容」判定（例如 10 分鐘內達 5 次），系統**暫時暫停該使用者的 AI 問答功能**，進入冷卻期（例如 30 分鐘）。
- 冷卻期間顯示提示：「*問答功能暫時關閉，請稍後再試或上傳更多學習資源。*」
- 此機制可透過 Redis (Memorystore) 的計數器實現，與現有的 API Rate Limiting 架構共用基礎設施。
