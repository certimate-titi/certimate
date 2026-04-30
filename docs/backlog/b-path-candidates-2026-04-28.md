# B 路徑簽核紀錄 — 2026-04-28

## 來源
2026-04-28 補完 F18 Bloom + F29 知識樹合併 step 時識別到 7 項規格 vs 現行設計落差。
全 5 features (F09/F14/F18/F26/F29) 已用 A 路徑容忍通過綠燈。

## 已落地（不在 backlog）

| 編號 | 項目 | Commit / 檔案 |
|------|------|---------------|
| B-18-2 | exam_result_service.get_result() 已內含 bloom_breakdown | commit `d4e8d20` 已完成（驗證確認）|
| B-29-1 | Dashboard `domainStrengths[]` 同時提供 `id` + `name` alias | dashboard_service._build_domain_strengths()（本次）|
| B-18-1 | GET /subjects/{id}/bloom-distribution + ?trend_by=year endpoint | bloom_analytics_service.py + subjects.py（本次）|

## 待 sprint 排程（backlog）

### B-18-3 — AI 教練 per-bloom 結構化建議（NICE TO HAVE）
- **規格**：「AI 教練應針對答錯的 understand 層次給予強化建議」
- **現況**：fallback summary 只把 weak Bloom 寫進 `ai_summary` 字串
- **建議實作**：
  - `bloom_breakdown` 內每項加 `coach_message` 欄位 OR 另起 `bloom_coach_suggestions` 區塊
  - Prompt 加結構化 schema（每個 weak bloom 一段 50 字內建議）
- **工期**：3-4h（service 改 + Prompt + schema + 前端）
- **A 路徑容忍**：step 透過 ai_summary 字串模糊匹配通過

### B-18-4 — 管理員考古題 HTTP 匯入 + AI 自動 Bloom 分類（NICE TO HAVE）
- **規格**：`POST /admin/historical-questions/import` + `POST /admin/historical-questions/auto-classify-bloom`
- **現況**：
  - 只有 CLI `app/scripts/import_exam_questions.py`（需 SSH 進機器跑）
  - Bloom 是 seed 寫死，無 AI 分類流程
- **建議實作**：
  - HTTP 包裝 CLI 邏輯 → admin router endpoint
  - 接 LLM 分類服務（Gemini 給每題打 Bloom 標籤 + 信心度）
  - audit log + 進度回報（SSE）
- **工期**：8-12h
- **A 路徑容忍**：step 模擬匯入 cycle，未實際打 LLM

## 保 A 路徑（不入 backlog）

| 編號 | 項目 | 保 A 理由 |
|------|------|----------|
| B-29-2 | 統一萃取 step 沒打 Gemini | 契約測試夠用，整合測試成本高 |
| B-29-3 | 「上傳 N 份教材」未建真 Resource | 對 depth=1 上限契約而言不需要真 Resource |
| B-BUG-1 | pomodoro step URL 單複數錯誤 | step 子領域已隨 @frontend 規範刪除 |

## 後續

backlog 兩項建議併入下一個 spec reconciliation sprint，與其他 271 failed scenario 一同處理。

---

## 新增 backlog（2026-04-28 e2e QA 衍生）

### F26 PDF Vision Gemini multimodal refactor（中）
- **問題**：`backend/app/services/exam_pdf_extraction_service.py` 直接用 Anthropic SDK 跑 Claude Vision；本地 dev 沒 Anthropic key（user 決議「本地 Anthropic 改用 claude code，雲端才用 Anthropic api」）→ 永遠 401
- **架構違規**：CLAUDE.md 規定 Gemini 為主 LLM，Anthropic 為雙 LLM 交叉驗證；PDF Vision 應用 Gemini multimodal（已有 valid key + `resource_parse_service` 已驗 pattern 可用）
- **建議**：把 `extract_questions_from_pdf` 換成 Gemini 2.5 Pro multimodal（client.files.upload + generate_content），保留 Anthropic 作為 cross-validation fallback
- **工期**：6-8h（含 prompt 對齊 + structured output schema）
- **影響**：F26 考綱逆向 e2e 本地驗證會通過

### uvicorn logger INFO invisibility（小）
- **問題**：uvicorn 預設不印 app logger INFO 級別到 stdout，本地 debug 看不到 `logger.info(...)` 訊息（如 F29 hook 的「Entering auto knowledge merge」）
- **建議**：uvicorn 啟動加 `--log-level info` 或在 `app/core/logging.py` 顯式設 `logging.basicConfig(level=logging.INFO)`
- **工期**：30 分鐘

### Pipeline 細粒度拆解 epic（A 方案 — 大）
- **觸發條件**：DAU 持續超過 1000 且 worker 整體成本 > $50/月，或 parse 階段失敗率 > 10%（持續 1 個月）
- **內容**：把 B+ 的單一 process_resource task 拆成 chunk / extract / parse / merge 4 個獨立 task type
- **新增**：`background_tasks` 表 + per-stage Cloud Tasks queue + dispatcher worker
- **預期效益**：高 DAU 時 worker 規格量身訂做、並行度提升、重試精細化（只重失敗階段）
- **工期**：5-7 天
- **盈虧平衡**：DAU 1500 後 12 個月內 TCO 反超

### 🚨 main service 明文 secrets（高優先 security ticket）
- **問題**：`certimate-titi` Cloud Run service 的 DATABASE_URL（含 password `CertiMate2026!`）、JWT_SECRET_KEY、SMTP_PASSWORD 是 `--set-env-vars` 明文，未走 Secret Manager
- **違反**：[feedback_secret_manager.md](file:///Users/simon/.claude/projects/-Users-simon-certimate-project/memory/feedback_secret_manager.md)「生產 API key 必走 Secret Manager + 專用 runtime SA，禁 --set-env-vars 明文」
- **發現於**：2026-04-29 cloud-engineer Pipeline Split epic 評估時
- **修補**：把三個 env 改用 `--update-secrets DATABASE_URL=db-url:latest,...` 注入；建 Secret Manager 對應 secrets
- **工期**：1h

### Gemini parse_job JSON 解析錯誤（高優先 — scaffold 生不出來）
- **發現於**：2026-04-30 EPIC pipeline-split RC18 後 e2e 驗證
- **症狀**：`run_parse_job` 跑到 Gemini API 但 response parse 失敗：
  ```
  gemini error: gemini returned non-JSON: { "markdown": "...", ... }
  ```
- **位置**：`backend/app/services/resource_parse_service.py` `_call_gemini_once` 或 JSON parse 區段
- **根因**：Gemini 回的是 wrapped JSON（含 markdown 字段），但 parser 期望 strict JSON 結構
- **影響**：parse_job 永遠 FAILED → scaffolds=0 → 學習鷹架功能在雲端不可用
- **建議修法**：
  1. 檢查 Gemini response_mime_type='application/json' 是否仍生效
  2. 或調整 parser 接受 wrapped JSON（從 response 中萃取 nested 結構）
  3. 加 unit test 用 fixture response 確保 parser 韌性
- **工期**：2-3h
