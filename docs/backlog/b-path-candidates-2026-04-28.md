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
