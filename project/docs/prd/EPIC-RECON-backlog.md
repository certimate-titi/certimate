# EPIC-RECON @skip Rules Backlog

**產出日期**: 2026-04-24
**來源**: EPIC-RECON（Features 01-07, 27）綠燈修復後遺留的 `@epic-recon @infra-heavy @skip` 規則
**總計**: 38 rules across 7 features
**用途**: 每條規則已標註所屬 epic 與解鎖條件，待 epic 排程時取消 @skip 並接線實作

---

## Epic 1 — AI Coach Safety Pipeline（16 rules，最大群）

統一 AI 教練（心智圖 + 錯題）的安全與參數層。所有規則共用 Gemini Flash 三維分類 Router + 配額扣減 + 輸出過濾。

| # | Feature:Line | Rule |
|---|---|---|
| 1 | 03b:94 | PRO_199 基礎教練（20 次/月），PRO_PLUS 深度策略 |
| 2 | 03b:138 | 心智圖教練 500 字輸入上限 |
| 3 | 03b:146 | 心智圖教練三維度安全分類 |
| 4 | 07:185 | 錯題教練 500 字輸入上限 |
| 5 | 07:193 | 依方案設定 max_tokens 上限 |
| 6 | 07:211 | 單次 session 10 輪上限 |
| 7 | 07:233 | Gemini Flash 三維分類（relevant/injection/answer_request） |
| 8 | 07:249 | Prompt injection 攔截（中英文） |
| 9 | 07:266 | 作答中禁止洩漏答案 |
| 10 | 07:294 | 超綱 5 次 / 10 分鐘 → 30 分鐘冷卻 |
| 11 | 07:315 | System prompt 保護 |
| 12 | 07:335 | PII 不得出現在回覆 |
| 13 | 07:344 | PII regex 後置過濾（Email/手機/身分證/信用卡） |
| 14 | 07:365 | 教育導向語氣（不當內容過濾） |
| 15 | 07:374 | EDU 加強版內容過濾（未成年） |
| 16 | 07:393 | 可驗證事實溯源引用 / 建議查證 |

**解鎖條件**: 安全 Router 實作 + `AiCooldown` tracking + `ai_usage_ledger` 扣減接線

---

## Epic 2 — AI 考題生成服務重構（5 rules）

四階段 Pipeline 的單元規則。現在服務端有整體流程，但各階段的可驗證分離尚未完成。

| # | Feature:Line | Rule |
|---|---|---|
| 1 | 04a:26 | `exam_mode=historical_only` 跳過 AI 四階段 |
| 2 | 04a:79 | 個人背景（年齡/學歷/職業）Prompt 注入 |
| 3 | 04a:127 | 階段 1 向量庫考綱 + Bloom 配比 |
| 4 | 04a:165 | 階段 2 原始考題生成 |
| 5 | 04a:183 | 階段 3 干擾項 + 詳解 |

**解鎖條件**: AI 生成服務重構 epic + stage-level mock/fixture 建立

---

## Epic 3 — Node Mastery / Progress Pipeline（EPIC-035 M3，7 rules）

練習與模擬考對 `node_mastery` + `knowledge_nodes` 的即時回寫。

| # | Feature:Line | Rule |
|---|---|---|
| 1 | 03:53 | 測驗完成後導航樹紅綠燈變色 |
| 2 | 03:103 | 練習作答即時更新知識圖譜 |
| 3 | 03:113 | 考綱擴展時進度平滑調降（稀釋） |
| 4 | 03b:169 | 知識節點依答對率顯示紅綠燈 |
| 5 | 03b:185 | 節點 ↔ 學習鷹架頁碼區間比對（TASK-02） |
| 6 | 07:167 | 錯題複習作答觸發 node_mastery 更新 |
| 7 | 07:488 | V3 練習模式 progress 即時 |

**解鎖條件**: EPIC-035 M3 練習 endpoint + wrong_review/practice exam_type 完成 + mastery_color 於節點 API 正確回傳

---

## Epic 4 — 歷史考古題 CI/CD 整合（3 rules）

| # | Feature:Line | Rule |
|---|---|---|
| 1 | 04:111 | 考古題模擬考模式 100% 抽歷史題 |
| 2 | 04:277 | 考古題從歷史題庫抽取真實題目（與 L111 重複，可合併） |
| 3 | 06:145 | 測驗結果 ForceGraph + 弱點分析（依賴 04a） |

**解鎖條件**: 歷史題庫匯入 CI/CD 排程完成 + exam_subject_codes → 節點對應 fixture

---

## Epic 5 — Playwright E2E 遷移（5 rules）

純前端 UI 互動，不適合 Behave step，應搬到 Playwright e2e。

| # | Feature:Line | Rule |
|---|---|---|
| 1 | 05:148 | 暫停/恢復計時器 |
| 2 | 05:159 | 總覽格 Modal 題目狀態 |
| 3 | 05:172 | 題目導航格點擊跳轉 |
| 4 | 07:419 | 錯題側邊列表切換 |
| 5 | 07:432 | 答案對比顯示 |

**解鎖條件**: Playwright e2e 子專案 scaffold 完成（目前僅後端 BDD）

---

## Epic 6 — Feature 27 AI 學習建議（1 rule）

| # | Feature:Line | Rule |
|---|---|---|
| 1 | 27:157 | AI 根據弱點節點生成學習路徑建議 |

**解鎖條件**: `/wrong-answer-map/subjects/{id}/ai-suggestions` endpoint 實作 + red-node 排序邏輯

---

## 優先級建議

| 優先 | Epic | 理由 |
|:---:|---|---|
| P0 | Epic 3 — Node Mastery | 影響核心學習循環（紅綠燈、練習回饋），已綁 EPIC-035 M3 |
| P1 | Epic 1 — AI Coach Safety | 上線前必須有安全閘，否則 prompt injection / 答案洩漏是 PR 災難 |
| P2 | Epic 2 — AI 考題生成重構 | 現有流程可用，細部驗證可延後 |
| P3 | Epic 4 — 歷史考古題 CI/CD | 依賴 crawler 排程，排程後自然拉動 |
| P4 | Epic 5 — Playwright 遷移 | 不阻塞功能，但應在 Production UI 改版前建好 |
| P5 | Epic 6 — Feature 27 AI 建議 | 單一 endpoint，附屬 Feature 27 改版時一併做 |

---

## 操作手冊

當某個 epic 進入執行階段：

1. 移除對應規則的 `@epic-recon @infra-heavy @skip` 標籤
2. 實作 / 擴充 step definitions
3. 跑 `behave tests/features/{N}-*.feature --tags=~@skip` 確認通過
4. 從本檔案移除已綠燈的 rule
5. Commit + push 觸發 CI/CD
