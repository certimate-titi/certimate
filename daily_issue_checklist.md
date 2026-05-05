# CertiMate Daily QA Issue Checklist
**產出時間**：2026-05-06 09:00 (Asia/Taipei)
**審查頁面數**：50 頁
**Feature File 數**：44 個
**發現問題總計**：🔴 8 + 🟠 5 + 🟡 5

---

## 頁面審查清單

### / — 首頁 (Landing Page)

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 立即免費註冊按鈕 | 按鈕 | ✅ 18-定價與升級引導 | ✅ 實作 | →/signup |
| 觀看展示連結 | 連結 | ✅ | ✅ | anchor scroll |

**問題**：無

---

### /login — 身分驗證

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email/密碼輸入 | 表單 | ✅ 01-身分驗證 | ✅ 實作 | |
| Google 登入按鈕 | 按鈕 | ✅ 01-身分驗證 | ✅ 實作 | |
| 記住我 checkbox | 控件 | ✅ 01-身分驗證 | ✅ 實作 | |
| 忘記密碼連結 | 連結 | ✅ 01-身分驗證 | ✅ 實作 | |
| 登入失敗訊息 | 空態/錯誤 | ✅ | ✅ | |

**問題**：無

---

### /signup — 註冊

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 姓名/Email/密碼輸入 | 表單 | ✅ 01-身分驗證 | ✅ 實作 | |
| 密碼強度指示條 | 顯示 | ✅ | ✅ | |
| 服務條款 modal | 互動 | ✅ | ✅ | |
| Google 註冊按鈕 | 按鈕 | ✅ | ✅ | |
| 免費註冊提交按鈕 | 按鈕 | ✅ | ✅ | |

**問題**：無

---

### /onboarding — 首次引導

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 4 步驟進度條 | 顯示 | ✅ 15-首次登入引導 | ✅ 實作 | |
| 科目選擇器 | 互動 | ✅ | ✅ | |
| 偏好設定表單 | 表單 | ✅ | ✅ | |
| 上一步/下一步按鈕 | 按鈕 | ✅ | ✅ | |
| 未選科目驗證訊息 | 空態 | ✅ | ✅ | |

**問題**：無

---

### /dashboard — 個人儀表板 ⭐核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Streak 計數器 | 顯示 | ✅ 13-儀表板 | ✅ 實作 | |
| Sprint/Standard/Mastery 模式 badge | 顯示 | ✅ 13-儀表板 | ✅ 實作 | |
| 4 核心指標卡 | 顯示 | ✅ 13-儀表板 | ✅ 實作 | 考試倒數/答題數/答對率/及格率 |
| 每日任務卡 | 顯示 | ✅ 13-儀表板 | ✅ 實作 | |
| 模式 tooltip 說明按鈕 | 互動 | 🔴 無 Scenario | ✅ 實作 | Feature 09/13 皆未覆蓋此互動 |
| 檔案上傳 (drag-drop) | 互動 | ✅ 02-資源上傳 | ✅ 實作 | |
| YouTube URL 解析按鈕 | 按鈕 | ✅ 02-資源上傳 | ✅ 實作 | |
| 儀表板無科目 CTA 卡 | 空態 | 🔴 無 Scenario | ✅ 實作 | 模態選科，非 /onboarding 流程，Feature 15 未涵蓋 |
| SubjectPickerModal (新增科目) | 互動 | ✅ 13-儀表板 | ✅ 實作 | |
| DomainRadarChart | 顯示 | ✅ 13-儀表板 | ✅ 實作 | |
| AnnouncementBanner | 顯示 | ✅ 24-公告管理 | ✅ 實作 | |
| 上傳失敗錯誤訊息 | 空態/錯誤 | 🟡 | ⚠️ 不足 | 僅顯示 exception 訊息，未查 resource_parse_jobs.failure_reason |

**問題**：
- 🔴 模式 tooltip 按鈕無對應 Feature Scenario
- 🔴 儀表板無科目時「開始選擇科目」CTA Modal 路徑，Feature 15 未覆蓋此 dashboard-level 行內加科目流程
- 🟡 上傳失敗狀態僅顯示例外訊息，未查 resource_parse_jobs 確認 failure_reason

---

### /knowledge — 知識庫主頁 ⭐核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 互動 | ✅ 03-知識心智圖 | ✅ 實作 | |
| 資源清單 (左側面板) | 顯示 | ✅ 11-資源庫管理 | ✅ 實作 | |
| ForceGraph 知識圖譜 | 顯示 | ✅ 03-知識心智圖 | ✅ 實作 | |
| MindMapTree 列表視圖 | 互動 | ✅ 03b | ✅ 實作 | |
| 節點詳情面板 | 互動 | ✅ 03-知識心智圖 | ✅ 實作 | |
| AI 教練對話面板 | 互動 | ✅ 03-知識心智圖 | ✅ 實作 | |
| 搜尋知識節點輸入 | 互動 | ✅ | ✅ | |
| 觸發解析按鈕 | 按鈕 | ✅ 02-資源上傳 | ✅ 實作 | |
| 刪除資源按鈕 | 按鈕 | ✅ 11-資源庫管理 | ✅ 實作 | |
| 全螢幕心智圖連結 | 連結 | ✅ 03b | ✅ 實作 | →/knowledge/mindmap |
| 個人錯題地圖連結 | 連結 | ✅ 27-錯題地圖 | ✅ 實作 | →/knowledge/wrong-answers |
| 資源面板摺疊按鈕 | 按鈕 | ✅ 03b Scenario | 🟠 缺失 | Feature 03b 有此 Scenario 但頁面無摺疊按鈕 |
| 節點掌握時灑花動畫 | 互動 | ✅ 03 spec | 🟠 缺失 | AI 教練送恭喜獎章動畫，頁面缺此實作 |
| 分享知識節點按鈕 | 按鈕 | 🔴 無 Scenario | ❌ 未實作 | Feature 03 提及分享，但無對應 UI 及 Scenario |
| PROCESSING 狀態解析說明 | 空態 | ✅ | 🟡 不足 | FAILED 有查 job，但 PROCESSING 中時空地圖僅顯示空畫面，無進度說明 |
| 空態查 resource_parse_jobs | 空態 | ✅ Layer 3 | ✅ 實作 | FAILED 已查詢 |

**問題**：
- 🔴 「分享知識節點」按鈕無 Feature Scenario 且未實作
- 🟠 Feature 03b 規格「資源面板摺疊按鈕」有 Scenario 但頁面缺對應 UI
- 🟠 Feature 03 規格「節點掌握時 AI 教練灑花動畫」有說明但頁面無 Confetti 實作
- 🟡 `/knowledge` 解析中 (PROCESSING) 狀態未向使用者說明進度，空圖譜時無法區分「PROCESSING 中」vs「FAILED」vs「從未上傳」

---

### /knowledge/mindmap — 全螢幕心智圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph/MindMapTree 切換 | 互動 | ✅ 03b | ✅ 實作 | |
| 節點點擊側邊面板 | 互動 | ✅ 03b | ✅ 實作 | |
| 開始練習此節點按鈕 | 按鈕 | ✅ 03b | ✅ 實作 | |
| 空態查 resource_parse_jobs | 空態 | ✅ Layer 3 | ✅ 實作 | |

**問題**：無

---

### /knowledge/wrong-answers — 錯題熱力圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 熱力圖節點 (顏色分級) | 顯示 | ✅ 27-錯題地圖 | ✅ 實作 | |
| 節點展開/收合 | 互動 | ✅ 27-錯題地圖 | ✅ 實作 | |
| 空態查 resource_parse_jobs | 空態 | ✅ Layer 3 | ✅ 實作 | |

**問題**：無

---

### /exam/setup — 測驗設定 ⭐核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| 文件/節點選擇清單 | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| AI 混合/考古題模式切換 | 按鈕 | ✅ 04-測驗設定 | ✅ 實作 | |
| 題目排列模式 (交錯/分組/依難度) | 按鈕 | ✅ 19-交錯練習 | ✅ 實作 | |
| 題目數量選擇 (tier 鎖定) | 按鈕 | ✅ 04-測驗設定 | ✅ 實作 | |
| 難度範圍滑桿 | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| 題型切換按鈕 | 按鈕 | ✅ 04-測驗設定 | ✅ 實作 | |
| 進階出題配方面板 (ULTRA) | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| 套用考古題分佈按鈕 | 按鈕 | ✅ 04-測驗設定 | ✅ 實作 | |
| 生成專屬模擬考按鈕 | 按鈕 | ✅ 04-測驗設定 | ✅ 實作 | |
| 空題庫提示文字 | 空態 | ✅ | 🟡 不足 | 靜態提示，未查 resourceParseService 取得 failure_reason |

**問題**：
- 🟡 `/exam/setup` 空題庫提示為靜態文字，未主動查 `resourceParseService.getStatus` 取得 failure_reason（此項為「已知改善中」，非新增問題）

---

### /exam/workspace — 模擬機考 ⭐核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 題目導覽格子 | 顯示 | ✅ 05-模擬機考 | ✅ 實作 | |
| 答案選項按鈕 | 按鈕 | ✅ 05-模擬機考 | ✅ 實作 | |
| 信心度選擇器 (😰😐😎) | 互動 | ✅ 20-信心度校準 | ✅ 實作 | |
| 標記複習按鈕 | 按鈕 | ✅ 05-模擬機考 | ✅ 實作 | |
| 計時器 | 顯示 | ✅ 05-模擬機考 | ✅ 實作 | |
| PomodoroTimer 元件 (read-only) | 顯示 | ✅ 21-番茄鐘 | ✅ 渲染 | 元件有渲染，但缺啟用/設定互動 UI |
| 番茄鐘啟用開關 | 按鈕 | ✅ 21-番茄鐘 Scenario | 🟠 缺失 | Feature 21 明確要求「啟用番茄鐘」按鈕 |
| 番茄鐘時長設定 | 互動 | ✅ 21-番茄鐘 Scenario | 🟠 缺失 | Feature 21 明確要求可設定專注/休息分鐘 |
| 繼續作答/開始休息按鈕 | 按鈕 | ✅ 21-番茄鐘 Scenario | 🟠 缺失 | Feature 21 Scenario「點擊繼續作答/開始休息」 |
| Certi 打氣語句 banner | 顯示 | ✅ 05-模擬機考 | ✅ 實作 | |
| 暫停/交卷 modal | 互動 | ✅ 05-模擬機考 | ✅ 實作 | |
| AI inference 判斷按鈕 | 按鈕 | 🔴 無 Scenario | ✅ 實作 | 保留我的答案/採信AI/略過；Feature 32/04a 未覆蓋此 UI |

**問題**：
- 🟠 Feature 21（番茄鐘）：workspace 頁缺番茄鐘啟用開關、時長設定 UI、「繼續作答/開始休息」選擇按鈕（PomodoroTimer 元件有渲染但上述互動 UI 缺失）
- 🔴 AI inference 判斷按鈕（`ai_inferred` 答案判斷，EPIC-035）無 Feature Scenario

---

### /exam/results — 測驗結果 ⭐核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 分數卡/及格指示 | 顯示 | ✅ 06-測驗結果 | ✅ 實作 | |
| AI 總評摘要 | 顯示 | ✅ 06-測驗結果 | 🟠 部分 | Feature 06 規定 FREE 用戶不應看到 AI 總評，但前端無 tier check |
| 信心度四象限分析 | 顯示 | ✅ 20-信心度校準 | ✅ 實作 | |
| Bloom 認知層次分析 | 顯示 | ✅ 18-題目分類 | ✅ 實作 | |
| 進入錯題本按鈕 | 按鈕 | ✅ 07-錯題複習 | ✅ 實作 | |
| 逐題解析連結 | 連結 | ✅ 06-測驗結果 | ✅ 實作 | |
| LinkedIn 分享按鈕 | 按鈕 | ✅ 06-測驗結果 | ✅ 實作 | |
| 下載成績圖卡按鈕 | 按鈕 | ✅ 06-測驗結果 | ✅ 實作 | html2canvas |
| 交錯練習模式標籤 | 顯示 | ✅ 19-交錯練習 | ✅ 實作 | |

**問題**：
- 🟠 Feature 06 規定 FREE 用戶「不應包含 AI 考後總評文字」並應顯示「升級至 PRO_199 方案的提示資訊」，前端 `/exam/results` 渲染 `aiSummary` 無 tier check

---

### /practice — 節點練習 ⭐核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 互動 | ✅ 32-節點練習 | ✅ 實作 | |
| 節點選擇清單 | 互動 | ✅ 32-節點練習 | ✅ 實作 | |
| 答案選項按鈕 | 按鈕 | ✅ 32-節點練習 | ✅ 實作 | |
| 信心度選擇器 | 互動 | ✅ 20-信心度校準 | ✅ 實作 | |
| 確認作答按鈕 | 按鈕 | ✅ 32-節點練習 | ✅ 實作 | |
| 回溯建議 banner | 顯示 | ✅ 28-難度遞進 | ✅ 實作 | |
| AI inference 判斷按鈕 | 按鈕 | 🔴 無 Scenario | ✅ 實作 | 保留/採信AI/略過；Feature 32 未覆蓋 |
| 空態查 resource_parse_jobs | 空態 | ✅ Layer 3 | ✅ 實作 | |
| 選擇其他節點/回知識圖譜 | 按鈕 | ✅ 32-節點練習 | ✅ 實作 | |

**問題**：
- 🔴 AI inference 判斷按鈕（EPIC-035）無 Feature Scenario

---

### /review — 錯題複習 ⭐核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 錯題清單側邊欄 | 顯示 | ✅ 07-錯題複習 | ✅ 實作 | |
| 題目+答案詳情面板 | 顯示 | ✅ 07-錯題複習 | ✅ 實作 | |
| AI Socratic 教練對話 | 互動 | ✅ 07-錯題複習 | ✅ 實作 | |
| 查看來源按鈕 | 按鈕 | ✅ | ✅ | |
| 空態查 examService.getRecentFailures | 空態 | ✅ Layer 3 | ✅ 實作 | |

**問題**：無

---

### /schedule — 學習排程 ⭐核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目排程卡片 | 顯示 | ✅ 09-學習排程 | ✅ 實作 | |
| 開始今日複習連結 | 連結 | ✅ 09-學習排程 | ✅ 實作 | |
| 空態「前往新增科目」連結 | 空態 | ✅ 09-學習排程 | ✅ 實作 | |

**問題**：無（排程為同步計算，Layer 3 不適用已確認）

---

### /account — 帳號設定

**問題**：無

---

### /account/my-subjects — 我的科目

**問題**：無

---

### /account/weekly-reports — 每週報告

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 週報清單 | 顯示 | ✅ 14-社群關懷 | ✅ 實作 | |
| 產生本週報告按鈕 | 按鈕 | ✅ 14-社群關懷 | ✅ 實作 | |
| 空週報清單狀態 | 空態 | ✅ | 🟡 不足 | reports 為空時無「尚無週報」提示訊息，靜默空白 |

**問題**：
- 🟡 `/account/weekly-reports` 報告清單為空時無明確說明文字（Layer 3 不適用；但缺少基本空態 UX 訊息）

---

### /pricing — 定價比較頁

**問題**：無

---

### /feedback — 意見反饋

**問題**：無

---

### /forgot-password、/reset-password — 密碼重設

**問題**：無（流程完整）

---

### /verify-email、/verify-email/sent — Email 驗證

**問題**：無（resend 失敗錯誤提示已修復於 2026-04-29）

---

### /invite/setup-password — 邀請密碼設定

**問題**：無

---

### /radar-demo — 開發展示頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 靜態雷達圖/長條圖展示 | 顯示 | 🔴 無 Feature 覆蓋 | N/A | 生產環境可訪問，無 auth guard |

**問題**：
- 🔴 `/radar-demo` 為開發沙盒頁，無任何 Feature Spec、無 @ignore 標記、無 auth/feature-flag 守衛，可在生產環境直接訪問

---

### /resources/[id]/candidates — 候選題目審核

**問題**：無（Feature 23 覆蓋確認，頁面已建立）

---

### /edu-console — B2B 機構管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| DPA 簽署 modal | 互動 | ✅ 10-B2B機構 | ✅ 實作 | |
| 學員清單表格 | 顯示 | ✅ 10-B2B機構 | ✅ 實作 | |
| CSV 批量邀請 | 互動 | ✅ 10-B2B機構 | ✅ 實作 | |
| 單個邀請表單 | 表單 | ✅ 10-B2B機構 | ✅ 實作 | |
| 學員清單空態說明 | 空態 | 🟡 | ⚠️ 不足 | 學員清單空時無明確說明或「邀請第一位學員」CTA |

**問題**：
- 🟡 `/edu-console` DPA 已簽署但學員清單為空時，缺明確的「下一步邀請學員」引導訊息

---

### /edu-console/student/[id] — 學員詳情

**問題**：無

---

### /super-admin/* — 平台管理後台 (各頁)

所有 super-admin 子頁面整體狀態良好。主要確認事項：

| 頁面 | Feature 覆蓋 | 狀態 |
|------|-------------|------|
| /super-admin/dashboard | ✅ 12-平台管理後台 | ✅ |
| /super-admin/users | ✅ 12 | ✅ |
| /super-admin/users/[id] | ✅ 12 | ✅ |
| /super-admin/platform-subjects | ✅ 12c + 34 | ✅ |
| /super-admin/default-resources | ✅ 34 | ✅ |
| /super-admin/exam-import | ✅ 32-考古題現代化匯入 | ✅ |
| /super-admin/finance | ✅ 12a | ✅ |
| /super-admin/moderation | ✅ 12b | ✅ |
| /super-admin/anomaly | ✅ 16-異常維修管理 | ✅ |
| /super-admin/audit-logs | ✅ 12 | ✅ |
| /super-admin/cost-monitor | ✅ 33-成本監控 | ✅ |
| /super-admin/retirement | ✅ 25-AI考題退場 | ✅ |
| /super-admin/prompt-templates | ✅ 30-Prompt模板 | ✅ |
| /super-admin/settings/* | ✅ 12c | ✅ (isSuperAdmin 守衛 audit 待補—已知) |

**問題**：無新增（super-admin 守衛改 isSuperAdmin 稽核為已知待辦）

---

## Feature File 覆蓋摘要

| Feature File | Scenario 數 (約) | @ignore/@wip 數 | 備註 |
|-------------|----------------|----------------|------|
| 01-身分驗證.feature | ~15 | 3 @manual | 完整 |
| 02-資源上傳.feature | ~11 | 2 @wip | |
| 03-知識心智圖.feature | ~10 | 0 | 分享節點 UI 缺 |
| 03a-知識心智圖生成.feature | ~4 | 0 | |
| 03b-知識心智圖導航.feature | ~12 | 0 | 資源面板摺疊按鈕缺實作 |
| 04-測驗設定.feature | ~10 | 0 | |
| 04a-AI考題生成服務.feature | ~10 | 0 | |
| 05-模擬機考.feature | ~8 | 0 | |
| 06-測驗結果.feature | ~10 | 0 | FREE tier AI 總評 paywall 缺 |
| 07-錯題複習與AI教練.feature | ~13 | 2 @playwright-e2e | |
| 08-訂閱管理.feature | ~13 | 0 | |
| 08a/08b | ~5 each | 0 | |
| 09-學習記憶排程.feature | ~10 | 0 | |
| 10-B2B機構管理後台.feature | ~55 | 0 | |
| 11-資源庫管理.feature | ~6 | 0 | |
| 12/12a/12b/12c | ~10 each | 0 | |
| 13-個人儀表板.feature | ~36 | 0 | 模式 tooltip 未覆蓋 |
| 14-社群歸屬.feature | ~6 | 0 | |
| 15-首次登入引導.feature | ~8 | 1 @wip | 儀表板無科目 CTA 路徑未覆蓋 |
| 16-異常維修管理.feature | ~7 | 0 | |
| 17-意見反饋.feature | ~7 | 0 | |
| 18-定價.feature | ~4 | 0 | |
| 18-題目分類.feature | ~6 | 0 | |
| 19-交錯練習.feature | ~8 | 0 | |
| 20-信心度校準.feature | ~10 | 0 | |
| 21-番茄鐘學習節奏.feature | ~6 | 0 | 番茄鐘啟用/設定 UI 缺 |
| 22-帳號設定.feature | ~6 | 0 | |
| 23-考古題題庫管理.feature | ~4 | 1 @wip | |
| 24-系統公告管理.feature | ~4 | 0 | |
| 25-AI考題退場.feature | ~36 | 0 | |
| 26-考綱逆向工程.feature | ~6 | 0 | |
| 27-個人化錯題地圖.feature | ~8 | 0 | |
| 28-階層式難度遞進.feature | ~8 | 0 | |
| 29-知識樹合併對齊.feature | ~6 | 0 | |
| 30-Prompt模板管理.feature | ~8 | 0 | |
| 31-多租戶安全.feature | 3 | 2 @wip | |
| 32-節點練習模式.feature | ~9 | 0 | AI inference 判斷按鈕未覆蓋 |
| 32-考古題現代化匯入.feature | ~6 | 0 | |
| 33-成本監控中心.feature | ~8 | 0 | |
| 34-預載科目Fork.feature | 9 | 0 | |

---

## 問題彙整

### 🔴 Feature 缺失（需新增 Scenario）

1. `/dashboard` — [模式 tooltip 按鈕] Sprint/Standard/Mastery 模式說明 tooltip 互動無對應 Feature Scenario（Feature 09/13 皆未覆蓋）
2. `/dashboard` — [空科目 CTA modal] 儀表板無科目時「開始選擇科目」dashboard-level modal 路徑，Feature 15 只覆蓋 /onboarding 流程，未涵蓋此行內加科目路徑
3. `/knowledge` — [分享知識節點按鈕] Feature 03 提及節點分享，但無對應 Scenario 且前端未實作此按鈕
4. `/exam/workspace` — [AI inference 判斷按鈕] 保留我的答案/採信AI/略過（EPIC-035）有 UI 實作但無 Feature Scenario（Feature 32/04a 皆未覆蓋）
5. `/practice` — [AI inference 判斷按鈕] 同上，練習頁的 AI 推斷答案判斷按鈕（EPIC-035）無 Feature Scenario
6. `/radar-demo` — [整頁] 開發沙盒頁無 Feature Spec、無 @ignore 標記、無 auth/flag 守衛，生產環境可訪問
7. `/account/weekly-reports` — [空態說明] Feature 14 未覆蓋「reports 為空」時應顯示的 UI 說明情境
8. `/exam/workspace` — [番茄鐘啟用入口] Feature 21 有「啟用番茄鐘」Scenario，但頁面缺此互動入口，使 Feature 21 scenario 無對應前端觸發路徑

### 🟠 實作缺失（Feature 存在但頁面缺功能）

1. `/exam/workspace` — Feature 21（番茄鐘）規定「啟用番茄鐘模式」、「設定專注/休息時長」、「點擊繼續作答/開始休息」三個 Scenario，頁面僅渲染 `PomodoroTimer` read-only 元件，缺啟用開關、時長設定 UI、休息/繼續選擇按鈕
2. `/knowledge` — Feature 03b Scenario「資源面板摺疊按鈕」存在，但頁面為 resizable 佈局，缺明確摺疊/展開按鈕
3. `/knowledge` — Feature 03 規格「AI 教練可能發送灑花恭喜獎章動畫（節點掌握時）」，頁面未實作 Confetti 或獎章動畫
4. `/exam/results` — Feature 06 規格 FREE 用戶「不應包含 AI 考後總評文字」並應顯示「升級至 PRO_199 提示資訊」，前端無 tier check 直接渲染 `aiSummary`
5. `/exam/workspace` — Feature 21 Scenario「番茄鐘計時結束 → 顯示休息/繼續選擇畫面」，頁面缺此選擇 UI（詳見 1 號）

### 🟡 空態需補強

1. `/dashboard` — 上傳後異步 parse 失敗僅顯示 exception 訊息，未查 `resource_parse_jobs.failure_reason`；用戶看不到實際失敗原因
2. `/knowledge` — PROCESSING 中的資源解析狀態未向使用者說明；空圖譜時無法區分「PROCESSING 中」vs「FAILED」vs「從未上傳」三種情境（FAILED 已處理，PROCESSING 情境缺說明）
3. `/account/weekly-reports` — `reports.length === 0` 時靜默空白，無「尚無週報」說明文字（cron 健康監控為維運層問題，但基本空態 UX 訊息應補）
4. `/edu-console` — DPA 已簽署但學員清單空時，缺明確「邀請第一位學員」引導訊息或 CTA
5. `/exam/setup` — 空題庫提示為靜態文字，未主動呼叫 `resourceParseService.getStatus()` 顯示 failure_reason（持續追蹤）

---

## Layer 3 空態查詢合規狀態摘要

| 頁面 | Layer 3 合規 | 查詢方法 |
|------|-------------|---------|
| /knowledge | ✅ 合規 | documentService.list + resourceParseService.getStatus（FAILED）；⚠️ PROCESSING 情境缺 |
| /knowledge/mindmap | ✅ 合規 | 同上 |
| /knowledge/wrong-answers | ✅ 合規 | 同上 |
| /practice | ✅ 合規 | 同上 |
| /review | ✅ 合規 | examService.getRecentFailures |
| /dashboard (上傳失敗) | ❌ 不合規 | 僅 exception 訊息 |
| /exam/setup (空題庫) | ❌ 不合規 | 靜態提示文字 |
| /schedule | ✅ 不適用 | 同步計算，無 async job 表 |
| /account/weekly-reports | ✅ 不適用 | WeeklyReport 無 status 欄位 |

---

*本報告由 CertiMate QA 自動稽核排程產出，每日覆蓋所有 50 個前端頁面與 44 個 Feature File。*
