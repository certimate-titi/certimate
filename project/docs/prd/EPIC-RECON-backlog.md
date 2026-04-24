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

## 優先級建議（依 ROI 排序）

評分：收益（1-5）÷ 成本（天數）= ROI 指數。收益考量核心體驗影響、付費轉換、解鎖規則數量；成本考量工期與依賴複雜度。

| 排序 | Epic | 收益 | 成本(天) | ROI | 主要理由 |
|:---:|---|:---:|:---:|:---:|---|
| 🥇 1 | **Epic 3 — Node Mastery Pipeline** | 5 | 3-5 | 🟢 **高** | 每次答題觸發的核心循環；紅綠燈直接影響用戶感知；一次解鎖 7 條跨 4 feature 規則；依賴都已備齊 |
| 🥈 2 | **Epic 4 — 歷史考古題 CI/CD** | 4 | 2-3 | 🟢 **高** | 付費差異化功能（考古題模擬考），用戶明確要求；crawler 已完成；2/3 條規則重複可合併 |
| 🥉 3 | **Epic 6 — Feature 27 AI 建議** | 2 | 0.5-1 | 🟢 **高** | 單一 endpoint 可在半天內完成；填充任務；Feature 27 其他規則已綠 |
| 4 | **Epic 1 — AI Coach Safety Pipeline** | 5 | 5-10 | 🟡 中 | 規則數最多（16）但工期最長；**上線前阻塞**（prompt injection / 答案洩漏 PR 災難）→ 若排上線則升為 P0 |
| 5 | **Epic 2 — AI 考題生成重構** | 2 | 4-5 | 🔴 低 | 現有 Pipeline 可用，stage-level 驗證是錦上添花；重構成本高於收益 |
| 6 | **Epic 5 — Playwright E2E 遷移** | 2 | 3-5 | 🔴 低 | 短期純 UI 驗證無直接用戶價值；長期有 scaffold 建好的節省效益，但應與 Production UI 改版一起做 |

### 執行建議路徑

**短衝刺（1 週內）**：依序做 Epic 3 → Epic 6 → Epic 4

這個組合可在 1 週內解鎖 **11 條規則**（7+1+3），覆蓋 4 個 feature，成本約 5-9 人日，全屬於用戶可感知的核心功能。

**中衝刺（2-3 週）**：Epic 1 AI Coach Safety（16 條規則，上線前必做）

若專案進入上線準備期，Epic 1 立即升為 P0 阻塞項。規模大但有明確 checklist。

**延後**：Epic 2（等 AI 品質回報變差再做）、Epic 5（等 Playwright scaffold 建好再做，或 UI 改版時一併）

### ROI 計算說明

收益刻度：
- 5 = 核心體驗 / 上線阻塞 / 規則數量 ≥ 7
- 3-4 = 付費差異化 / 用戶可感知 / 規則數量 3-5
- 1-2 = 錦上添花 / 規則數量 ≤ 2 或純內部改善

成本刻度：以人日估算，含 step 實作 + fixture + 接線 + BDD 驗證。

---

## 操作手冊

當某個 epic 進入執行階段：

1. 移除對應規則的 `@epic-recon @infra-heavy @skip` 標籤
2. 實作 / 擴充 step definitions
3. 跑 `behave tests/features/{N}-*.feature --tags=~@skip` 確認通過
4. 從本檔案移除已綠燈的 rule
5. Commit + push 觸發 CI/CD
