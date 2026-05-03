# CertiMate Daily QA Issue Checklist
**產出時間**：2026-05-04 10:00 (Asia/Taipei)
**審查頁面數**：49 頁
**Feature File 數**：44 個
**發現問題總計**：🔴 4 + 🟠 4 + 🟡 3

---

## 頁面審查清單

### /dashboard — 使用者主控台

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| StreakCounter 連勝計數器 | 顯示 | Feature 13 L73 | ✅ 已實作 | |
| SubjectSwitcher 科目切換 | 互動 | Feature 13 L40 | ✅ 已實作 | |
| DailyQuestCard 每日任務 | 顯示 | Feature 13 L96 | ✅ 已實作 | |
| DomainRadarChart 領域雷達圖 | 圖表 | Feature 13 L228 | ✅ 已實作 | |
| 備考模式標籤 Sprint/Standard/Mastery | 顯示 | Feature 13 L379 | ✅ 已實作 | |
| 快速上傳（檔案/YouTube）| 互動 | Feature 02 | ✅ 已實作 | |
| 待辦提醒 activityItems | 顯示 | Feature 13 L59 | ✅ 已實作 | |
| ScheduleWeekCard | 顯示 | Feature 09 | ✅ 已實作 | |
| SubjectPickerModal 新增科目 | 互動 | Feature 15 | ✅ 已實作 | |
| ULTRA 共讀橫幅 StudyBuddy | 顯示 | ❌ 無覆蓋 | 🟠 只有程式碼注解 | 需補 Feature + 實作 |

**問題**：
- 🔴 ULTRA 共讀橫幅（`/community/online-count` API）無 Feature Scenario 亦無實作，僅有 comment `// Ultra: Co-study counter — requires backend /community/online-count API`

---

### /knowledge — 知識地圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph / MindMapTree 視圖切換 | 互動 | Feature 03b L231 | ✅ 已實作 | |
| 節點點擊 → 詳情面板 | 互動 | Feature 03 | ✅ 已實作 | |
| AI 教練對話框 | 互動 | Feature 07 | ✅ 已實作 | |
| 搜尋框 | 互動 | Feature 03 | ✅ 已實作 | |
| 學習鷹架 ScaffoldMaterial/Notebook/Replay | 顯示 | Feature 03 | ✅ 已實作 | |
| FAILED 文件 Layer 3 查詢 | 空態 | CLAUDE.md 規則 | ✅ 已實作 | |
| 節點掌握度顏色（mastery_color）| 顯示 | Feature 27 | ✅ 已實作 | |
| 錯題熱力圖 | 顯示 | Feature 27 | 🟠 僅用 mastery_color 近似 | 無獨立 heatmap 層 |

**問題**：
- 🟠 Feature 27（個人化錯題地圖）要求知識樹節點顯示「紅/橘/綠色視覺化個人弱點分佈」，目前僅使用 mastery_color 近似，未有獨立錯題地圖熱力圖層覆蓋

---

### /knowledge/mindmap — 全螢幕知識地圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph / MindMapTree 切換 | 互動 | Feature 03b L231 | ✅ 已實作 | |
| 節點點擊互動（詳情面板/跳轉）| 互動 | ❌ 無覆蓋 | 🟠 僅 setSelectedNodeId | 無視覺反饋面板 |
| Layer 3 空態查詢 | 空態 | CLAUDE.md 規則 | ✅ 已實作 | |
| 返回按鈕 | 互動 | Feature 03b | ✅ 已實作 | |

**問題**：
- 🔴 全螢幕地圖頁節點點擊後互動行為無 Feature Scenario 覆蓋；現行實作僅 `setSelectedNodeId`，無詳情面板顯示（既有 ToDoList 已記錄，首見 2026-05-01）

---

### /exam/setup — 測驗設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 知識節點選擇（系統考古題庫）| 互動 | Feature 04 | ✅ 已實作 | |
| 文件選擇 | 互動 | Feature 04 | ✅ 已實作 | |
| 題數選擇（含方案限制鎖）| 互動 | Feature 04 | ✅ 已實作 | |
| 難度 Slider | 互動 | Feature 04 | ✅ 已實作 | |
| 題型偏好（單選/填空/計算）| 互動 | Feature 04 | ✅ 已實作 | |
| 出題模式（AI混合/考古題）| 互動 | Feature 04 | ✅ 已實作 | |
| 題目排列模式（交錯/分組/依難度）| 互動 | Feature 19 | ✅ 已實作 | |
| 進階出題配方 Bloom 比例 | 互動 | Feature 04 | ✅ 已實作（isUltra\|isAdmin）| |
| 生成進度 ExamLoadingOverlay | 顯示 | Feature 04 | 🟠 假動畫 | Feature 04 指定 SSE 推送 |

**問題**：
- 🟠 Feature 04 規格描述測驗生成應使用 SSE 推送即時進度；目前 ExamLoadingOverlay 為模擬假階段動畫，未訂閱 SSE 端點（既有 ToDoList 已記錄，首見 2026-05-01）

---

### /exam/workspace — 模擬機考作答

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 倒數計時器 | 顯示 | Feature 05 | ✅ 已實作 | |
| 題目導航 Grid | 互動 | Feature 05 | ✅ 已實作 | |
| 標記待複查 Flag | 互動 | Feature 05 | ✅ 已實作 | |
| 暫停/繼續 | 互動 | Feature 05 | ✅ 已實作 | |
| 番茄鐘 PomodoroTimer | 互動 | Feature 21 | ✅ 已實作 | |
| 信心度校準（😰😐😎）| 互動 | Feature 20 | ✅ 已實作 | |
| 提交確認 Modal | 互動 | Feature 05 | ✅ 已實作 | |
| AI 教練打氣語句（Certi）| 顯示 | Feature 05 | 🟠 無實作 | workspace/page.tsx 無此 UI |

**問題**：
- 🟠 Feature 05 Scenario「開始測驗前 AI 教練（Certi）基於使用者狀態動態生成打氣語句」，workspace/page.tsx 無對應 UI 元素（既有 ToDoList 已記錄，首見 2026-04-29）

---

### /exam/results — 測驗結果

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 分數顯示 + 及格 Confetti | 顯示 | Feature 06 | ✅ 已實作 | |
| 進步/退步比較 | 顯示 | Feature 06 | ✅ 已實作 | |
| Bloom 認知層次分析 | 顯示 | Feature 18/06 | ✅ 已實作 | |
| ForceGraph 知識圖譜 | 圖表 | Feature 06 | ✅ 已實作 | |
| 分享至 LinkedIn | 互動 | Feature 06 | ✅ 已實作 | |
| 下載成績卡片（PNG）| 互動 | Feature 06 | ✅ 已實作（html2canvas）| |
| 逐題解析入口 | 互動 | Feature 06 | ✅ 已實作 | |
| AI 教練介入卡片（連續退步）| 顯示 | Feature 06 | ✅ 已實作 | |
| 交錯練習標籤 | 顯示 | Feature 19 | ✅ 已實作 | |

---

### /practice — 自由練習模式

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 知識節點選擇列表 | 互動 | Feature 32 | ✅ 已實作 | |
| 答題 + 即時反饋 | 互動 | Feature 32/07 | ✅ 已實作 | |
| 信心度校準（😰😐😎）| 互動 | Feature 20 | ✅ 已實作 | |
| Layer 3 空態查 FAILED 文件 | 空態 | CLAUDE.md 規則 | ✅ 已實作 | |
| blindInferenceService AI 盲點 | 互動 | Feature 07 | ✅ 已實作 | |
| 空態「選擇其他節點」按鈕 | 互動 | Feature 32 | ✅ 已實作 | |
| 階層式難度回溯（depth 3→2→1）| 邏輯 | Feature 28 | 🟡 未查後端回溯 | practice 頁無自動回溯 UI |

**問題**：
- 🟡 Feature 28（階層式難度遞進）規定「在進階節點答錯時系統自動回溯到父節點」；practice/page.tsx 僅載入所選節點題目，無自動回溯邏輯，空態亦無「切換至父節點」提示

---

### /review — 錯題複習與 AI 教練

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 錯題側邊列表 | 顯示 | Feature 07 | ✅ 已實作 | |
| AI 教練蘇格拉底對話 | 互動 | Feature 07 | ✅ 已實作 | |
| KaTeX 數學公式渲染 | 顯示 | Feature 07 | ✅ 已實作（rehype-katex）| |
| 引用來源切換 | 互動 | Feature 07 | ✅ 已實作 | |
| 科目切換器 | 互動 | Feature 07 | ✅ 已實作 | |
| 全部答對空態 | 空態 | Feature 07 | 🟡 未查 job 表 | 違反 Layer 3 規則 |

**問題**：
- 🟡 `wrongQuestions.length === 0` 時直接顯示「全部答對！」但未查詢 `exam_generation_jobs` / `resource_parse_jobs`，無法區分「真正全答對」vs「job FAILED 導致無錯題記錄」（既有 ToDoList 已記錄，待後端補 API）

---

### /schedule — 學習排程

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 各科目學習模式顯示 | 顯示 | Feature 09 | ✅ 已實作 | |
| 今日推薦題數 | 顯示 | Feature 09 | ✅ 已實作 | |
| 開始今日複習按鈕 | 互動 | Feature 09 | ✅ 已實作 | |
| 空態（無科目）| 空態 | Feature 09 | 🟡 未查 schedule job 表 | 違反 Layer 3 規則 |

**問題**：
- 🟡 `recs.length === 0` 時直接顯示「尚無備考科目」，未查詢 schedule 相關 job 表（既有 ToDoList 已記錄，待後端補 API）

---

### /account — 帳號設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 個人資料 Tab | 互動 | Feature 22 | ✅ 已實作 | |
| 訂閱方案 Tab | 顯示 | Feature 08 | ✅ 已實作 | |
| 安全 Tab（密碼/刪除）| 互動 | Feature 22 | ✅ 已實作 | |
| 成就 Tab | 顯示 | Feature 13 | ✅ 已實作 | |
| 通知偏好設定 | 互動 | Feature 22 | 🟠 僅 localStorage | Feature 22 規格為 API 操作 |
| 使用量顯示 | 顯示 | Feature 22 | ✅ 已實作 | |

**問題**：
- 🟠 通知偏好（daily_reminder / pre_exam_reminder / weekly_report）僅存 `localStorage`；Feature 22 規格描述為後端 API 操作，規格與實作不同步（既有 ToDoList 已記錄，首見 2026-05-01）

---

### /account/weekly-reports — 歷史週報

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 週報列表 | 顯示 | Feature 14 | ✅ 已實作 | |
| 手動觸發本週報告 | 互動 | Feature 14 | ✅ 已實作 | |
| 空態（無週報）| 空態 | Feature 14 | 🟡 未查週報 job 表 | 違反 Layer 3 規則 |

---

### /account/my-subjects — 我的自訂科目

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 自建科目列表 | 顯示 | Feature 13 L357 | ✅ 已實作 | |
| 刪除自建科目 | 互動 | Feature 13 L357 | ✅ 已實作 | |

---

### /pricing — 定價頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 四方案比較表 | 顯示 | Feature 18 | ✅ 已實作 | |
| 升級按鈕（ECPay）| 互動 | Feature 08a | ✅ 已實作 | |
| 現有方案標示 | 顯示 | Feature 18 | ✅ 已實作 | |

---

### /feedback — 意見反饋

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 回饋類型選擇 | 互動 | Feature 17 | ✅ 已實作 | |
| 表單提交（含截圖）| 互動 | Feature 17 | ✅ 已實作 | |
| 歷史回饋紀錄 | 顯示 | Feature 17 | ✅ 已實作 | |

---

### /onboarding — 新手引導

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 四步驟流程（Welcome/Subject/Preferences/Confirm）| 互動 | Feature 15 | ✅ 已實作 | |
| SubjectPicker 科目選擇 | 互動 | Feature 15 | ✅ 已實作 | |

---

### /edu-console — B2B 機構管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 學生名單 | 顯示 | Feature 10 | ✅ 已實作 | |
| CSV 批次匯入 | 互動 | Feature 10 | ✅ 已實作 | |
| 批次邀請 | 互動 | Feature 10 | ✅ 已實作 | |
| 早期預警規則 | 顯示 | Feature 10 | ✅ 已實作 | |
| DPA 簽署 Modal | 互動 | Feature 10 | 🔴 無實作 | Feature 10 L58 要求 DPA 簽署 |

**問題**：
- 🔴 Feature 10 L58-65 規定「機構管理員首次匯入學生前須簽署資料處理合約（DPA）」；`edu-console/page.tsx` 完全無 DPA 相關 UI（modal/consent）

---

### /super-admin/dashboard — 平台管理員主控台

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| KPI 指標卡（DAU/MAU/MRR/AI token）| 顯示 | Feature 12 | ✅ 已實作 | |
| 趨勢折線圖 | 圖表 | Feature 12 | ✅ 已實作 | |
| 快速跳轉入口 | 互動 | Feature 12 | ✅ 已實作 | |

---

### /super-admin/cost-monitor — 成本監控

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| AI 供應商用量（Anthropic/Gemini/Voyage）| 顯示 | Feature 33 | ✅ 已實作 | |
| GCP 服務分類 | 顯示 | Feature 33 | ✅ 已實作 | |
| 預算告警狀態 | 顯示 | Feature 33 | ✅ 已實作 | |
| 趨勢面積圖 | 圖表 | Feature 33 | ✅ 已實作 | |

---

### /super-admin/anomaly — 異常事件管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 異常列表（含狀態流轉）| 顯示 | Feature 16 | ✅ 已實作 | |
| 批次修復（多選 + 批次 PATCH）| 互動 | Feature 16 | ✅ 已實作 | |
| 建立維修任務 Modal | 互動 | Feature 16 | ✅ 已實作 | |
| 維修排程 Modal | 互動 | Feature 16 | ✅ 已實作 | |
| 全站維修模式按鈕 | 互動 | Feature 16 | ✅ 已實作 | |

---

### /super-admin/moderation — 內容審核

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 審核佇列 | 顯示 | Feature 12b | ✅ 已實作 | |
| 通過/拒絕/標記動作 | 互動 | Feature 12b | ✅ 已實作 | |
| 意見反饋管理 Tab | 互動 | Feature 17 | ✅ 已實作 | |
| AI 濫用監控 Tab | 顯示 | Feature 12b | ✅ 已實作 | |

---

### /super-admin/finance — 財務管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 營收指標（MRR/訂閱數）| 顯示 | Feature 12a | ✅ 已實作 | |
| 交易紀錄列表 + 篩選 | 互動 | Feature 12a | ✅ 已實作 | |
| 退款審核（需 OTP）| 互動 | Feature 12a | ✅ 已實作 | |
| 匯出 CSV | 互動 | Feature 12a | ✅ 已實作 | |

---

### /super-admin/users — 使用者管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 使用者搜尋/過濾 | 互動 | Feature 12 | ✅ 已實作 | |
| 停權/恢復按鈕 | 互動 | Feature 12 | ✅ 已實作 | |
| 分頁 | 互動 | Feature 12 | ✅ 已實作 | |
| 邀請使用者 | 互動 | Feature 12 | ✅ 已實作 | |

---

### /super-admin/prompt-templates — Prompt 模板管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 模板列表（含類別篩選）| 顯示 | Feature 30 | ✅ 已實作 | |
| 搜尋 | 互動 | Feature 30 | ✅ 已實作 | |
| 新增/編輯模板 | 互動 | Feature 30 | ✅ 已實作 | |
| A/B 測試（設定頁面）| 互動 | Feature 30 | ✅ 已實作（詳情頁）| |

---

### /super-admin/exam-import — 考古題匯入

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 上傳 JSON | 互動 | Feature 23/32 | ✅ 已實作 | |
| 匯入任務監控 Dashboard | 顯示 | Feature 23 | ✅ 已實作 | |
| FAILED 任務錯誤訊息 | 顯示 | Feature 23 | ✅ 已實作 | |
| 效能指標 Tab | 顯示 | Feature 23 | ✅ 已實作 | |

---

### /super-admin/retirement — 退役題庫批次任務

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 退場掃描 / 硬刪除 / 重算任務按鈕 | 互動 | Feature 25 | ✅ 已實作 | |
| 放榜通知任務 | 互動 | Feature 25 | ✅ 已實作 | |

---

### /super-admin/settings/* — 系統設定子頁群

| 頁面 | 功能 | Feature 覆蓋 | 備註 |
|------|------|-------------|------|
| /settings（AI 路由）| AI 模型路由 | Feature 12c | ✅ 已實作 |
| /settings/plans | 方案配額 | Feature 12c | ✅ 已實作 |
| /settings/announcements | 站內公告 | Feature 24 | ✅ 已實作 |
| /settings/flags | Feature Flags | Feature 12c | ✅ 已實作 |
| /settings/admins | 管理員帳號 | Feature 12c | ✅ 已實作 |
| /settings/version | 版本資訊 | Feature 12c L260 | ✅ 已實作 |

---

### 其他頁面（簡易稽核）

| 路徑 | 說明 | 主要 Feature | 狀態 |
|------|------|-------------|------|
| /login | Email / Google SSO 登入 | Feature 01 | ✅ |
| /signup | 電子郵件註冊 | Feature 01 | ✅ |
| /forgot-password | 密碼重設申請 | Feature 01 | ✅ |
| /reset-password | 密碼重設表單 | Feature 01 | ✅ |
| /verify-email | 驗證中間頁 | Feature 01 | ✅ |
| /verify-email/sent | 重寄驗證信 | Feature 01 | ✅ |
| /invite/setup-password | 邀請設定密碼 | Feature 12c | ✅ |
| /resources/[id]/candidates | 候選題目審核 | Feature 23 | ✅ |
| /super-admin/default-resources | 預設資源管理 | Feature 34 | ✅ |
| /super-admin/platform-subjects | 平台科目管理 | Feature 34/12c | ✅ |
| /super-admin/audit-logs | 稽核日誌 | Feature 12 | ✅ |
| /super-admin/users/[userId] | 用戶詳情 | Feature 12 | ✅ |
| /super-admin/settings/api-keys | API 金鑰 | Feature 12c | ✅ |
| /radar-demo | 開發沙盒 | — | 開發工具，無需 Feature |
| /page（首頁）| Landing page | — | 靜態，無需 Feature |

---

## Feature File 覆蓋摘要

| Feature File | Scenario 數 | @ignore/@wip 數 | 無對應頁面元素 |
|-------------|------------|----------------|--------------|
| 01-身分驗證 | 54 | 0 | 無 |
| 02-資源上傳 | 31 | 2 | 無 |
| 03-知識心智圖 | 16 | 0 | 無 |
| 03a-知識心智圖生成 | 4 | 0 | 無 |
| 03b-知識心智圖導航 | 25 | 0 | 無 |
| 04-測驗設定 | 27 | 0 | 無 |
| 04a-AI考題生成服務 | 18 | 0 | 無 |
| 05-模擬機考 | 19 | 0 | AI打氣語句未實作 |
| 06-測驗結果 | 20 | 0 | 無 |
| 07-錯題複習與AI教練 | 44 | 0 | 無 |
| 08-訂閱管理 | 25 | 0 | 無 |
| 08a-綠界金流串接 | 10 | 0 | 無 |
| 08b-付款後權限更新 | 10 | 0 | 無 |
| 09-學習記憶排程 | 13 | 0 | 無 |
| 10-B2B機構管理後台 | 55 | 0 | DPA 簽署 UI 未實作 |
| 11-資源庫管理 | 13 | 0 | 無 |
| 12-平台管理後台 | 35 | 0 | 無 |
| 12a-平台管理後台-財務管理 | 13 | 0 | 無 |
| 12b-平台管理後台-內容審核 | 10 | 0 | 無 |
| 12c-平台管理後台-系統設定 | 28 | 0 | 無 |
| 13-個人儀表板與成就系統 | 43 | 0 | 無 |
| 14-社群歸屬與主動關懷 | 10 | 0 | 無 |
| 15-首次登入引導與學習歷程建立 | 38 | 1 | 無 |
| 16-異常維修管理 | 13 | 0 | 無 |
| 17-意見反饋 | 23 | 0 | 無 |
| 18-定價與升級引導 | 9 | 0 | 無 |
| 18-題目分類與考試趨勢分析 | 8 | 0 | 已在 exam/results bloomBreakdown 覆蓋 |
| 19-交錯練習 | 8 | 0 | 無 |
| 20-信心度校準 | 13 | 0 | 無 |
| 21-番茄鐘學習節奏 | 15 | 0 | 無 |
| 22-帳號設定與個人偏好 | 8 | 0 | 通知偏好 API 未實作 |
| 23-考古題題庫管理 | 12 | 1 | 無 |
| 24-系統公告管理 | 4 | 0 | 無 |
| 25-AI考題退場與放榜確認 | 36 | 0 | 無 |
| 26-考綱逆向工程 | 16 | 0 | 無 |
| 27-個人化錯題地圖 | 10 | 0 | knowledge 頁 mastery_color 近似，無獨立熱力圖層 |
| 28-階層式難度遞進 | 15 | 0 | practice 頁無自動回溯邏輯 |
| 29-知識樹合併對齊 | 21 | 0 | 後端自動觸發，無前端操作需求 |
| 30-Prompt模板管理 | 30 | 0 | 無 |
| 31-多租戶安全與資料隔離 | 16 | 2 | 無（後端 RLS 已啟用）|
| 32-節點練習模式 | 9 | 0 | 無 |
| 32-考古題現代化匯入 | 22 | 0 | 無 |
| 33-成本監控中心 | 29 | 0 | 無 |
| 34-預載科目Fork | ~9 | 0 | 無 |

---

## 問題彙整

### 🔴 Feature 缺失（需新增 Scenario 或補完實作）

1. `/dashboard` — ULTRA 共讀橫幅（StudyBuddyBanner）：UI 僅有 comment `// Ultra: Co-study counter — requires backend /community/online-count API`，缺前端實作與 Feature Scenario；首見 2026-04-27，至今仍未解決
2. `/knowledge/mindmap` — 全螢幕地圖頁節點點擊後的互動行為（詳情面板/跳轉）無任何 Feature Scenario 覆蓋；現行實作僅 `setSelectedNodeId`，無視覺反饋；首見 2026-05-01，至今未解決
3. `/edu-console` — Feature 10 L58 規定「首次匯入學生前須簽署 DPA（資料處理合約）」，頁面無任何 DPA 相關 UI；首見 2026-05-04
4. `/practice` — Feature 28（階層式難度遞進）規定答錯進階節點時自動回溯父節點，頁面無自動回溯邏輯；首見 2026-05-04

### 🟠 實作缺失（Feature 存在但頁面缺功能）

1. `/exam/setup` — Feature 04 規格要求 SSE 推送即時進度，前端 ExamLoadingOverlay 為模擬假動畫；首見 2026-05-01，持續未解決
2. `/exam/workspace` — Feature 05 規格「AI 教練（Certi）打氣語句」workspace/page.tsx 無對應 UI；首見 2026-04-29，持續未解決
3. `/account` — 通知偏好僅存 localStorage，Feature 22 規格為後端 API 操作；首見 2026-05-01，持續未解決
4. `/knowledge` — Feature 27（個人化錯題地圖）要求獨立錯題熱力圖層；目前僅用 mastery_color 近似，無獨立熱力圖覆蓋層；首見 2026-05-04

### 🟡 空態需補強

1. `/review` — `wrongQuestions.length === 0` 空態未查詢 `exam_generation_jobs` / `resource_parse_jobs`；前置條件為後端補 API（已在 ToDoList 記錄）
2. `/schedule` — `recs.length === 0` 空態未查詢 schedule job 表；前置條件為後端補 API（已在 ToDoList 記錄）
3. `/account/weekly-reports` — `reports.length === 0` 空態未查詢週報產生 job；前置條件為後端補 API（已在 ToDoList 記錄）
