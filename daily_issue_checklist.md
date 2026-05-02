# CertiMate Daily QA Issue Checklist
**產出時間**：2026-05-03 01:08 (Asia/Taipei)
**審查頁面數**：49 頁
**Feature File 數**：44 個
**發現問題總計**：🔴 3 + 🟠 8 + 🟡 5

---

## 頁面審查清單

### /dashboard — 個人儀表板

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| AnnouncementBanner | 顯示 | ✅ Feature 24 | ✅ 實作 | |
| StreakCounter（學習連勝） | 顯示 | ✅ Feature 13 L73 | ✅ 實作 | |
| DomainRadarChart（領域雷達圖） | 顯示 | ✅ Feature 13 L228 | ✅ 實作 | |
| SubjectSwitcher（科目切換器） | 互動 | ✅ Feature 13 L40 | ✅ 實作 | |
| DailyQuestCard（每日任務） | 顯示 | ✅ Feature 13 L96 | ✅ 實作 | |
| ScheduleWeekCard（本週複習） | 顯示 | ✅ Feature 09 | ✅ 實作 | |
| 備考模式標籤 Sprint/Standard/Mastery | 顯示 | ✅ Feature 13 L379 | ✅ 實作 | |
| StudyBuddyBanner（ULTRA 共讀橫幅） | 顯示 | 🔴 無 Feature Scenario | ⚠️ 有程式碼邏輯但 feature 未覆蓋 | 需補 Feature Scenario |

---

### /knowledge — 知識心智圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph / MindMapTree / Document 三視圖 | 互動 | ✅ Feature 03b L231 | ✅ 實作 | |
| Batch reparse failed 全部失敗空態 | 按鈕 | ✅ Feature 03b | ✅ 實作（L794 batchReparseFailed） | |
| FREE 用戶 AI 追問限制（3次/節點） | 付費牆 | ✅ Feature 03b L88 | ✅ 實作（剩 {freeQueriesLeft}/3） | |
| FAILED 文件查詢 failure_reason | 空態補強 | ✅ Feature 03b 四種空態 | ✅ 實作（resourceParseService.getStatus()） | |
| 全螢幕地圖節點點擊互動面板 | 互動 | 🔴 無任何 Scenario | ⚠️ 僅 setSelectedNodeId，無視覺反饋 | 已於上次巡檢列入 |

---

### /exam/setup — 測驗設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 題數上限 FREE=10 / PRO=50 / PRO_PLUS=100 / ULTRA=無限 | 限制 | ✅ Feature 04 | 🟠 **BUG: PRO_PLUS_399 max=50，規格應為 100** | TIER_QUESTION_LIMITS L31 |
| 升級提示文字（PRO_199 → PRO_PLUS 100 題） | 顯示 | ✅ Feature 04 L65 | 🟠 **BUG: 文字錯誤**，顯示「升級 ULTRA 最多 100 題以上」應為「升級 PRO_PLUS 最多可出 100 題」 | L30 |
| Bloom 認知層次配比（ULTRA 專屬） | 付費牆 | ✅ Feature 04 | 🟠 **BUG: 以 `isAdmin` 守衛**，ULTRA 付費用戶無法存取 | L699 |
| 測驗生成進度 SSE 串流 | 即時回饋 | ✅ Feature 04 | 🟠 **缺失**: 使用假動畫 overlay，未實際訂閱 SSE 端點 | L37-42 |
| interleaved / grouped / sequential 排列模式 | 互動 | ✅ Feature 19 | ✅ 實作（三按鈕 UI） | |
| 考古題模式（historical_only） | 互動 | ✅ Feature 04 L118 | ✅ 實作 | |

---

### /exam/workspace — 測驗作答

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| PomodoroTimer | 計時 | ✅ Feature 21 | ✅ 實作 | |
| 信心度標記三個圖示（😰😐😎） | 互動 | ✅ Feature 20 | 🟠 **缺失**: 答案選項下方無信心度標記 UI | 已於上次巡檢列入 |
| 開考前 AI 打氣（Certi 角色） | 顯示 | ✅ Feature 05 | 🔴 **缺失**: 頁面程式碼無任何 Certi 打氣 UI | 已於上次巡檢列入 |

---

### /exam/results — 測驗結果

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 分享至 LinkedIn 按鈕（placeholder 即將推出） | 按鈕 | ✅ Feature 06 L136-141 | 🟠 **規格不符**: 規格要「即將推出」提示，實作已做真實 LinkedIn 分享 | Feature Scenario 需更新 |
| 下載成績卡片（placeholder 即將推出） | 按鈕 | ✅ Feature 06 L143-148 | 🟠 **規格不符**: 規格要「即將推出」提示，實作已用 html2canvas 真實下載 | Feature Scenario 需更新 |
| 排列模式標籤「交錯練習」及提示文字 | 顯示 | ✅ Feature 19 L85-89 | 🟠 **缺失**: 結果頁無 question_order_mode 標籤顯示 | |
| 知識地圖（ForceGraph）灰色節點說明 | 顯示 | ✅ Feature 06 | ✅ 實作（灰色節點保留） | 無明確說明文字 |
| 逐題解析連結 | 按鈕 | ✅ Feature 06 | ✅ 實作（/review?examId=... L240） | |

---

### /practice — 節點練習

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 節點熟練度徽章（green/yellow/red/gray） | 顯示 | ✅ Feature 32 | ✅ 實作（mastery_color L336-346） | |
| no-questions 空態「前往出題」按鈕 | 空態 | ✅ Feature 32 | ✅ 實作（L384） | |
| ?nodeId=N 直接導航 | 路由 | ✅ Feature 32 | ✅ 實作 | |
| no-questions 空態查詢 resource_parse_jobs | Layer 3 | ✅ Feature 03b | 🟡 **未查 job 表**：僅文字提示，未調用 API 取得 failure_reason | |
| 信心度標記（😰😐😎） | 互動 | ✅ Feature 20 | 🟠 **缺失**: answering phase 無信心度標記 UI（確認：L610 僅為結果顯示，非作答中標記） | 已於上次巡檢列入 |

---

### /review — 錯題複習

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| KaTeX 數學公式渲染 | 顯示 | ✅ Feature 07 | ✅ 實作（MathContent + rehype-katex） | |
| FREE 用戶毛玻璃遮罩 | 付費牆 | ✅ Feature 07 | ✅ 實作 | |
| AI 教練引用來源切換 | 互動 | ✅ Feature 07 | ✅ 實作 | |
| wrongQuestions === 0 空態查詢 job 表 | Layer 3 | ✅ 規則要求 | 🟡 **未查 job 表**：「全部答對！」未確認後端 job 狀態 | 已於上次巡檢列入 |

---

### /schedule — 備考計劃

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Sprint/Standard/Mastery 模式顯示 | 顯示 | ✅ Feature 13 | ✅ 實作 | |
| recs.length === 0 空態查詢 schedule job | Layer 3 | 規則要求 | 🟡 **未查 job 表**：直接顯示「尚無備考科目」 | 已於上次巡檢列入 |

---

### /pricing — 訂閱方案

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| FREE / PRO / PRO+ / ULTRA 方案卡片 | 顯示 | ✅ Feature 18 | ✅ 實作 | |
| EDU 學生方案說明區塊 | 顯示 | ✅ Feature 18 | ✅ 實作（頁面底部 EDU 說明 div L196-216） | 前次誤報為缺失，已確認存在 |

---

### /account — 帳戶設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 通知偏好（daily_reminder 等）儲存方式 | 後端同步 | ✅ Feature 22 | 🟠 **規格不符**: 存 localStorage，規格描述為 API 操作 | 已於上次巡檢列入 |

---

### /account/weekly-reports — 學習週報

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| reports.length === 0 空態查詢 weekly report job | Layer 3 | 規則要求 | 🟡 **未查 job 表**：直接顯示「尚無週報」 | 已於上次巡檢列入 |

---

### /super-admin/anomaly — 異常管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 批次修復 UI 與 Scenario | 互動 | ✅ Feature 16 | 🟠 **缺失**: 批次修復 Scenario 存在但頁面無對應 UI | 已於上次巡檢列入 |

---

## 問題彙整（本次新發現標記 ★）

### 🔴 Feature 缺失（UI 元素無任何 Feature Scenario）

| # | 頁面 | 元素 | 說明 |
|---|------|------|------|
| 1 | `/dashboard` | StudyBuddyBanner | 無 Feature Scenario 覆蓋 |
| 2 | `/knowledge` | 全螢幕地圖節點點擊互動面板 | 僅 setSelectedNodeId，無視覺反饋且無 Scenario |
| 3 | `/exam/workspace` | 開考前 AI 打氣（Certi 角色） | Feature 05 有 Scenario 但頁面完全未實作 UI |

---

### 🟠 實作缺失（Feature Scenario 存在但頁面功能有誤或未實作）

| # | 頁面 | 問題 | Feature | 嚴重度 |
|---|------|------|---------|--------|
| 1 ★ | `/exam/setup` | PRO_PLUS_399 題數上限 code=50 但規格應為 100 | Feature 04 L71-83 | P1 |
| 2 ★ | `/exam/setup` | PRO_199 升級提示文字錯誤（寫 ULTRA 應寫 PRO_PLUS） | Feature 04 L65 | P2 |
| 3 | `/exam/setup` | Bloom 認知層次配比以 `isAdmin` 守衛，ULTRA 用戶無法存取 | Feature 04 | P1 |
| 4 | `/exam/setup` | 測驗生成進度用假動畫 overlay，未實際訂閱 SSE 端點 | Feature 04 | P2 |
| 5 | `/exam/results` | 排列模式標籤「交錯練習」及提示文字未顯示 | Feature 19 L85-89 | P2 |
| 6 | `/exam/results` | LinkedIn 分享與成績卡片下載已實作，但 Feature Scenario 仍寫「即將推出」→ Scenario 需更新 | Feature 06 L136-148 | P3（Spec 落後） |
| 7 | `/exam/workspace` | 信心度標記（😰😐😎）在作答中未顯示 | Feature 20 | P2 |
| 8 | `/practice` | 信心度標記（😰😐😎）在 answering phase 未顯示 | Feature 20 | P2 |
| 9 | `/account` | 通知偏好存 localStorage，規格要求 API | Feature 22 | P2 |
| 10 | `/super-admin/anomaly` | 批次修復功能 Scenario 存在但頁面無 UI | Feature 16 | P2 |

---

### 🟡 空態補強（空態未查詢 Job 表違反 Layer 3 規則）

| # | 頁面 | 空態條件 | 應查詢的 Job 表 |
|---|------|---------|---------------|
| 1 | `/practice` | phase === 'no-questions' | resource_parse_jobs (failure_reason) |
| 2 | `/review` | wrongQuestions.length === 0 | exam_generation_jobs / resource_parse_jobs |
| 3 | `/schedule` | recs.length === 0 | schedule_jobs 或相關 job 表 |
| 4 | `/account/weekly-reports` | reports.length === 0 | weekly_report_jobs (cron) |
| 5 | `/knowledge` | documents 與 nodes 皆空時 | resource_parse_jobs (failure_reason) |

---

## 修復優先序

### P1 — 本週必修（影響付費用戶功能）
1. **`/exam/setup` PRO_PLUS_399 max=100**（TIER_QUESTION_LIMITS L31 改 `max: 100`）
2. **`/exam/setup` PRO_199 升級提示文字**（L30 改為「升級 PRO_PLUS 最多可出 100 題」）
3. **`/exam/setup` Bloom 守衛改為 `isUltra`**（L699 `isAdmin` → `isUltra`）

### P2 — 兩週內（功能正確性）
4. `/exam/results` 補排列模式標籤「交錯練習」
5. `/exam/workspace` + `/practice` 補信心度標記 UI（Feature 20）
6. `/account` 通知偏好改為 API 儲存（Feature 22）
7. `/exam/setup` SSE 進度串流（替換假動畫）
8. `/super-admin/anomaly` 補批次修復 UI

### P3 — 排期中（規格補強）
9. Feature 06 更新 Scenario（LinkedIn 分享與成績卡片下載已實作，需更新 spec 反映實際狀態）
10. 五個 🟡 空態頁面補查 job 表
11. Feature 05 實作開考前 Certi 打氣 UI
12. StudyBuddyBanner 補 Feature Scenario

---

*本 checklist 由 TiTi Commander 排程巡檢自動產出。*
