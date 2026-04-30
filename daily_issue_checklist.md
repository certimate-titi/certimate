# CertiMate Daily QA Issue Checklist
**產出時間**：2026-05-01 10:30 (Asia/Taipei)
**審查頁面數**：49 頁（其中重點深析 10 頁）
**Feature File 數**：44 個
**發現問題總計**：🔴 5 + 🟠 8 + 🟡 6

---

## 頁面審查清單

### /dashboard — 使用者主控台首頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目切換器 (SubjectSwitcher) | 互動 | Feature 13 L40 Rule 已覆蓋 | 已實作 | |
| 連勝計數器 (StreakCounter) | 統計顯示 | Feature 13 L73 已覆蓋 | 已實作 | |
| 每日任務 (DailyQuestCard) | 互動 | Feature 13 L96 已覆蓋 | 已實作 | |
| 核心指標卡（倒數/答題數/答對率/預測及格率） | 統計顯示 | Feature 13 L59 已覆蓋 | 已實作 | |
| 備考模式 Badge（Sprint/Standard/Mastery） | 互動 Tooltip | Feature 13 L379-411 已覆蓋 | 已實作 | |
| 快速上傳區（PDF/Office/音訊/影片/圖片） | 互動表單 | Feature 13 L164-195 已覆蓋 | 已實作 | |
| YouTube 連結解析 | 互動表單 | Feature 13 L184 已覆蓋 | 已實作 | |
| 待辦提醒 (activityItems) | 清單 | Feature 13 L59 已覆蓋 | 已實作 | |
| DomainRadarChart（領域雷達圖） | 圖表 | Feature 13 L228 已覆蓋 | 已實作 | |
| StudyBuddyBanner (ULTRA 共讀計數) | 橫幅 | 無 Feature 覆蓋 | 程式碼僅有 comment，未實作 | 🔴 Feature 缺失 |

**問題**：StudyBuddyBanner 功能（ULTRA 共讀人數）在程式碼中僅留有 comment（`{/* Ultra: Co-study counter — requires backend /community/online-count API */}`），既無 Feature Scenario 覆蓋，也未實作。

---

### /knowledge — 知識地圖頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 左側知識樹/圖譜 (ForceGraph + MindMapTree) | 圖表互動 | Feature 03b L231 + 03 已覆蓋 | 已實作 | |
| 右側節點詳情面板 (NodeDetailPanel) | 面板 | Feature 03b L64-76 已覆蓋 | 已實作 | |
| AI 教練聊天框 | 互動 | Feature 03b L96-114 已覆蓋 | 已實作 | |
| 搜尋框 | 互動 | Feature 03 搜尋規則已覆蓋 | 已實作 | |
| 資源刪除確認 Modal | 互動 | Feature 03 已覆蓋 | 已實作 | |
| 資源上傳入口（導向 dashboard） | 互動按鈕 | 無 Scenario 覆蓋此導向路徑 | 點擊導向 `/dashboard` 而非 modal | 🟠 導航行為無回歸保護 |
| 節點練習按鈕 | 互動 | Feature 32 導航規則已覆蓋 | 已實作 | |
| FREE 用戶使用次數計數器 | 提示 | Feature 03b L89 已覆蓋 | 已實作 | |
| ScaffoldMaterial / ScaffoldNotebook / ScaffoldReplayCard | 學習鷹架 | Feature 03a 已覆蓋 | 已實作 | |
| 空態（mindMapNodes.length === 0） | 空態 | 有文字說明 | 未查詢 resource_parse_jobs | 🟡 空態未補強 |

**問題**：
1. 知識頁的新增資源按鈕（`+ 新增資源`）導向 `/dashboard`，Feature 03 無 Scenario 覆蓋此路徑，導航目標改變時無回歸保護。
2. 空態顯示「上傳教材後系統會自動生成」，但未主動查詢 `resource_parse_jobs` 確認是否有 FAILED job，違反 Layer 3 規則。

---

### /knowledge/mindmap — 全螢幕知識地圖頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph 動態圖譜 | 圖表 | Feature 03b L231 已覆蓋 | 已實作 | |
| MindMapTree 列表模式 | 圖表 | Feature 03b L231 已覆蓋 | 已實作 | |
| 科目切換器 | 互動 | Feature 03b L23 已覆蓋 | 已實作 | |
| 視圖切換按鈕（動態圖譜/列表模式） | 互動 | Feature 03b L231 已覆蓋 | 已實作 | |
| 返回按鈕（回 /knowledge） | 導航 | 隱含於導航規格 | 已實作 | |
| 空態（mindMapNodes.length === 0） | 空態 | 有文字說明 | 未查詢 resource_parse_jobs | 🟡 空態未補強 |
| 節點點擊後無詳情面板 | 互動 | 全螢幕地圖頁節點點擊無 Scenario | 僅 setSelectedNodeId，無視覺反饋 | 🔴 Feature 缺失 |

**問題**：
1. `/knowledge/mindmap` 頁節點點擊僅呼叫 `setSelectedNodeId`，無任何詳情面板彈出或跳轉邏輯。Feature 03b 對「全螢幕地圖頁節點點擊的互動行為」無對應 Scenario。
2. 空態未查詢 `resource_parse_jobs`。

---

### /practice — 自由練習模式頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 葉節點列表（選擇知識節點） | 選擇互動 | Feature 32 已覆蓋 | 已實作 | |
| 節點掌握度徽章（%/顏色） | 顯示 | Feature 32 已覆蓋 | 已實作 | |
| 題目進度條 | 顯示 | Feature 32 已覆蓋 | 已實作 | |
| 答案選項（ABCD） | 互動 | Feature 32 已覆蓋 | 已實作 | |
| 答題回饋（詳解/進度更新） | 顯示 | Feature 32 已覆蓋 | 已實作 | |
| AI 推論揭示（ai_inferred 題目） | 互動 | Feature 20 blindInference 已覆蓋 | 已實作 | |
| 信心度標記（😰😐😎） | 互動 | Feature 20 要求此 UI | 練習頁面無此 UI 元素 | 🟠 實作缺失 |
| no-questions 空態 | 空態 | Feature 32 L67 已覆蓋 | 有文字提示，未查詢 resource_parse_jobs | 🟡 空態未補強 |
| 科目切換器 | 互動 | Feature 19/32 已覆蓋 | 已實作 | |

**問題**：
1. Feature 20（信心度校準）要求「答案選項下方應出現信心度標記列：😰 😐 😎」（L117），但 `/practice` 頁的答題回合中完全無此 UI 元素，功能缺失。
2. `no-questions` 空態（`phase === 'no-questions'`）僅以文字引導，未主動查詢 `resource_parse_jobs` 取得 `failure_reason`。

---

### /review — 錯題複習簿頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 左側錯題列表 | 側邊欄 | Feature 07 已覆蓋 | 已實作 | |
| 中央題目與答案對比 | 顯示 | Feature 07 已覆蓋 | 已實作 | |
| 詳細解析（毛玻璃付費牆） | 顯示 | Feature 07 已覆蓋 | 已實作 | |
| AI 蘇格拉底教練聊天 | 互動 | Feature 07 已覆蓋 | 已實作 | |
| 來源查看 Popover | 互動 | Feature 07 已覆蓋 | 已實作 | |
| MathContent KaTeX 渲染 | 顯示 | Feature 07 已覆蓋 | 已實作 | |
| 空態（wrongQuestions.length === 0） | 空態 | Feature 07 未覆蓋空態 job 查詢 | 顯示「全部答對！」但未查詢 job 表 | 🟡 空態未補強 |
| 科目切換器 | 互動 | Feature 07 L26 已覆蓋 | 已實作 | |

**問題**：`wrongQuestions.length === 0` 時直接顯示「全部答對！太厲害了！」，但未查詢後端 `exam_generation_jobs` / `resource_parse_jobs` 確認是否有 FAILED job 造成無錯題記錄（違反 Layer 3 規則）。

---

### /exam/setup — 考試設定頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目切換器 | 互動 | Feature 04 L22 已覆蓋 | 已實作 | |
| 知識節點選擇（考古題題庫） | 勾選清單 | Feature 04 已覆蓋 | 已實作 | |
| 題數選擇（訂閱方案限制） | 按鈕群 | Feature 04 已覆蓋 | 已實作 | |
| 難度滑桿 | 互動 | Feature 04 已覆蓋 | 已實作 | |
| 題目排列模式（🔀/📦/📈） | 按鈕群 | Feature 19 已覆蓋 | 已實作 | |
| 出題模式（AI 混合/考古題） | 切換按鈕 | Feature 04 已覆蓋 | 已實作 | |
| 進階出題配方（Bloom 配比/節點比例） | 折疊面板 | Feature 04 ULTRA 配比規格 | 僅 isAdmin 可見，ULTRA 一般用戶無法使用 | 🟠 實作缺失 |
| 生成中動畫 (ExamLoadingOverlay) | 狀態 | Feature 04 SSE 推送規格 | 前端使用模擬動畫非 SSE | 🟠 實作缺失 |

**問題**：
1. Feature 04 規格「ULTRA 方案可自訂 Bloom 認知層級比例」，但程式碼中進階配方面板使用 `isAdmin` 判斷，ULTRA_1599 一般使用者（非 admin）無法使用此功能，與規格不一致。
2. Feature 04 規格要求透過 SSE 推送生成進度（四階段事件），前端使用 ExamLoadingOverlay 模擬動畫，非實際 SSE 訂閱。

---

### /exam/workspace — 模擬考作答頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 計時器（倒數/低於 5 分紅色警示） | 顯示 | Feature 05 已覆蓋 | 已實作 | |
| 番茄鐘計時器 (PomodoroTimer) | 互動 | Feature 21 已覆蓋 | 已實作 | |
| 題號導覽網格 | 互動 | Feature 05 已覆蓋 | 已實作 | |
| 標記複查按鈕 | 互動 | Feature 05 已覆蓋 | 已實作 | |
| 暫停/交卷/總覽 Modal | 互動 | Feature 05 已覆蓋 | 已實作 | |
| AI 教練「打氣語句」（開始測驗前） | 情感互動 | Feature 05 已定義 | 頁面無任何對應 UI | 🟠 實作缺失 |
| 信心度標記 UI（😰😐😎） | 互動 | Feature 20 要求 | 頁面無此 UI | 🟠 實作缺失 |
| beforeunload 離頁警告 | 瀏覽器事件 | Feature 05 已覆蓋 | 已實作 | |

**問題**：
1. Feature 05 Scenario「開始測驗前 AI 基於使用者狀態動態生成打氣語句，顯示 AI 教練角色（Certi）打氣介面」，頁面完全無此 UI 元素。
2. Feature 20（信心度校準）要求作答時可標記信心度（😰😐😎），但 `/exam/workspace` 完全無此 UI。

---

### /exam/results — 考試結果頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 分數與及格判斷 | 顯示 | Feature 06 已覆蓋 | 已實作 | |
| 撒花動畫 (Confetti) | 情感互動 | Feature 06 已覆蓋 | 實作觸發條件 >= 80，規格為通過（>= 70）| |
| Bloom 認知層次分析 | 圖表 | Feature 04/18 已覆蓋 | 已實作 | |
| 知識點弱點分析（進度條） | 圖表 | Feature 06 已覆蓋 | 已實作 | |
| 知識圖譜 (ForceGraph) | 圖表 | Feature 06 L190 已覆蓋 | 已實作 | |
| 分享至 LinkedIn 按鈕 | 互動 | Feature 06：應為 placeholder | 實際已直接開啟分享視窗 | 🔴 規格與實作不同步 |
| 下載成績卡片按鈕 | 互動 | Feature 06：應為 placeholder | 實際已用 html2canvas 實作 | 規格需更新 |
| AI 分析摘要 | 顯示 | Feature 06 已覆蓋 | 已實作 | |
| 錯題本入口 | 導航 | Feature 06 已覆蓋 | 已實作 | |
| 免責聲明 | 文字 | Feature 06 已覆蓋 | 已實作 | |

**問題**：Feature 06 明確規定「分享到 LinkedIn 按鈕應顯示為 placeholder 未實作狀態」，但目前頁面已實際開啟 LinkedIn 分享視窗。Feature 需更新以反映現有實作狀態。

---

### /account — 個人帳戶設定頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 個人資料 Tab（顯示名稱/年齡/學歷/職業） | 表單 | Feature 22 已覆蓋 | 已實作 | |
| 訂閱與帳單 Tab | 顯示 | Feature 08/22 已覆蓋 | 已實作 | |
| 安全性 Tab（密碼修改/刪除帳號） | 表單 | Feature 22 已覆蓋 | 已實作 | |
| 偏好設定 Tab（深色模式/通知） | 互動 | Feature 22 已覆蓋 | 通知偏好存 localStorage 非 API | 🟠 實作與規格不符 |
| 成就與歷程 Tab | 顯示 | Feature 13 L123 已覆蓋 | 已實作 | |

**問題**：通知偏好（daily_reminder / pre_exam_reminder / weekly_report）目前存 localStorage，但 Feature 22 規格描述為 API 操作。

---

### /pricing — 訂閱方案定價頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 四方案比較卡片 | 顯示 | Feature 18 已覆蓋 | 已實作 | |
| PRO_PLUS_399「進階 AI 教練」 | 顯示 | Feature 03/18 有覆蓋 | `included: false`，與規格矛盾 | 🔴 規格不一致 |
| 目前方案標記 | 顯示 | Feature 18 已覆蓋 | 已實作 | |
| 升級按鈕（ECPay 結帳） | 互動 | Feature 08a 已覆蓋 | 已實作 | |

**問題**：`PRO_PLUS_399` 方案的「進階 AI 教練」功能顯示為 `included: false`，但 Feature 03 明定 PRO_PLUS_399 可使用完整 AI 教練。定價頁資訊誤導用戶。

---

### /schedule — 學習排程頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目排程卡片（Sprint/Standard/Mastery） | 顯示 | Feature 09 已覆蓋 | 已實作 | |
| 「開始今日複習」按鈕 | 互動 | Feature 09 已覆蓋 | 已實作 | |
| 空態（recs.length === 0） | 空態 | 顯示「尚無備考科目」 | 未查詢 schedule job 表 | 🟡 空態未補強 |

---

## Feature File 覆蓋摘要

| Feature File | Scenario 數（估計） | @ignore/@wip 數 | 無對應頁面元素 |
|-------------|-------------------|----------------|--------------|
| 01-身分驗證 | 40+ | 3 (@manual) | 無 |
| 02-資源上傳 | 30+ | 4 (@prd-033 @wip) | 分片上傳後端 Pipeline 前端無直接 UI |
| 03-知識心智圖 | 8 active | 0 | 左右 75%/25% 佈局 Scenario vs 靈活佈局實作 |
| 03a-知識心智圖生成 | 4 | 0 | 無 |
| 03b-知識心智圖導航 | 15+ | 0 | 全螢幕地圖頁節點點擊詳情無實作 |
| 04-測驗設定 | 25+ | 0 | ULTRA Bloom 配比自訂僅 Admin 可用 |
| 04a-AI考題生成服務 | 10+ | 0 | SSE 進度推送（前端用模擬動畫） |
| 05-模擬機考 | 20+ | 0 | AI 打氣語句無實作、信心度標記無實作 |
| 06-測驗結果 | 20+ | 0 | LinkedIn/下載按鈕 Scenario 已過時 |
| 07-錯題複習與AI教練 | 15+ | 0 | 無 |
| 08-訂閱管理 | 10+ | 0 | 無 |
| 09-學習記憶排程 | 10+ | 0 | 無 |
| 13-個人儀表板與成就系統 | 36 | 0 | ULTRA 共讀橫幅 |
| 17-意見反饋 | 10+ | 0 | 無 |
| 18-定價與升級引導 | 10+ | 0 | PRO_PLUS 進階 AI 教練功能矩陣錯誤 |
| 19-交錯練習 | 8 | 0 | 無 |
| 20-信心度校準 | 13+ | 0 | 練習頁/機考頁缺信心度 UI |
| 21-番茄鐘學習節奏 | 15 | 0 | 無 |
| 22-帳號設定與個人偏好 | 12 | 0 | 通知偏好存 localStorage 非 API |
| 27-個人化錯題地圖 | 8+ | 0 | 無 |
| 32-節點練習模式 | 9 | 0 | 無 |

---

## 問題彙整

### 🔴 Feature 缺失（需新增 Scenario 或更新規格）

1. `/dashboard` — StudyBuddyBanner（ULTRA 共讀在線人數橫幅）無 Feature Scenario 覆蓋，程式碼僅留 comment 未實作（首見：2026-04-27）
2. `/knowledge/mindmap` — 全螢幕地圖頁節點點擊後的互動行為（詳情面板/導航）無 Feature Scenario 覆蓋；實作僅 setSelectedNodeId 無任何視覺反饋（首見：2026-05-01）
3. `/exam/results` — Feature 06 規格要求「LinkedIn 分享為 placeholder 即將推出提示」，但實作已直接開啟分享視窗；Feature 規格與實作不同步，需更新（首見：2026-04-30）
4. `/pricing` — PRO_PLUS_399「進階 AI 教練」在 PLANS 陣列中設定 `included: false`，與 Feature 03 規格矛盾，定價頁誤導用戶（首見：2026-04-30）
5. `/account` — 通知偏好（daily/pre-exam/weekly_report）目前存 localStorage，Feature 22 規格描述為 API 操作；規格與實作不同步（首見：2026-05-01）

### 🟠 實作缺失（Feature 存在但頁面缺功能）

1. `/exam/workspace` — Feature 05：開始測驗前 AI 教練（Certi）打氣語句介面，頁面完全無此 UI 元素（首見：2026-04-29）
2. `/exam/workspace` — Feature 20：作答時信心度標記 UI（😰😐😎），頁面完全無此 UI（首見：2026-05-01）
3. `/practice` — Feature 20：練習模式答題時信心度標記 UI（😰😐😎），頁面完全無此 UI（首見：2026-05-01）
4. `/exam/setup` — Feature 04：ULTRA 方案 Bloom 配比自訂功能僅 `isAdmin` 可用，ULTRA_1599 一般用戶無法存取，與規格不符（首見：2026-05-01）
5. `/exam/setup` — Feature 04：SSE 進度推送，前端使用 ExamLoadingOverlay 模擬動畫非真正 SSE 訂閱（首見：2026-05-01）
6. `/knowledge` — Feature 03：「+ 新增資源」按鈕導向 `/dashboard` 而非就地上傳，Feature 03 無 Scenario 覆蓋此導航路徑，改動無回歸保護（首見：2026-04-28）
7. `/super-admin/anomaly` — Feature 16「批次修復」互動元素缺乏對應 UI 與 Scenario 覆蓋（首見：2026-04-24）
8. `/account` — Feature 22：通知偏好應透過 API 儲存，目前僅存 localStorage（首見：2026-05-01）

### 🟡 空態需補強（需查 Job 表）

1. `/review` — `wrongQuestions.length === 0` 時顯示「全部答對！」但未查詢 `exam_generation_jobs` / `resource_parse_jobs` 確認是否 FAILED（違反 Layer 3，首見：2026-04-28）
2. `/practice` — `no-questions` 空態有文字 hint 但未查詢 `resource_parse_jobs` 取得 `failure_reason`（首見：2026-04-24）
3. `/knowledge/mindmap` — 空態顯示「上傳教材後系統會自動生成」但未查詢 parse jobs 確認 FAILED 狀態（首見：2026-05-01）
4. `/knowledge` — 空態（documents 及 nodes 皆為空）時，需補充查詢 `resource_parse_jobs` 的 FAILED 狀態（首見：2026-05-01）
5. `/schedule` — `recs.length === 0` 顯示「尚無備考科目」，未查詢 schedule job 失敗記錄（首見：2026-04-29）
6. `/account/weekly-reports` — `reports.length === 0` 顯示「尚無週報」，未查詢週報 cron job 失敗記錄（首見：2026-04-30）
