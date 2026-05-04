# CertiMate Daily QA Issue Checklist
**產出時間**：2026-05-05 01:11 (Asia/Taipei)
**審查頁面數**：50 頁
**Feature File 數**：44 個
**發現問題總計**：🔴 3 + 🟠 2 + 🟡 2

---

## 頁面審查清單

### / — 首頁 (Landing Page)

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 立即開始按鈕（→ /signup） | 連結 | N/A（行銷頁） | ✅ 實作 | |
| 方案定價區三個「免費試用」按鈕 | 按鈕 | N/A | ✅ 實作 | |
| 了解功能連結（#features） | 連結 | N/A | ✅ 實作 | |

---

### /login — 身分驗證

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email/密碼登入表單 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| Google SSO 按鈕 | 按鈕 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 忘記密碼連結 | 連結 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 顯示/隱藏密碼切換 | 按鈕 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 前往 /signup 連結 | 連結 | ✅ | ✅ 實作 | |

---

### /signup — 註冊

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email/密碼註冊表單 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 服務條款同意勾選框 | 表單 | ✅ 01-身分驗證.feature Scenario「未勾選同意服務條款操作失敗」 | ✅ 實作 | |
| 顯示服務條款 modal | 按鈕 | ✅ | ✅ 實作 | |
| 密碼強度指示條 | 顯示 | ✅ 01-身分驗證.feature Scenario Outline「密碼強度指示條」 | ✅ 實作 | |
| 提交註冊按鈕 | 按鈕 | ✅ | ✅ 實作 | |
| authService.signup | API | ✅ | ✅ 實作 | |

---

### /verify-email — 驗證 Email

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 驗證確認訊息 | 顯示 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 重寄驗證信連結 | 連結 | ✅ | ✅ 實作 | |
| authService.verifyEmail | API | ✅ | ✅ 實作 | |

---

### /verify-email/sent — 驗證信已送出

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 重寄驗證信按鈕 | 按鈕 | ✅ | ✅ 實作 | |
| 返回登入連結 | 連結 | ✅ | ✅ 實作 | |
| authService.resendVerification | API | ✅ | ✅ 實作 | |

---

### /forgot-password — 忘記密碼

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email 輸入表單 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 送出重設信按鈕 | 按鈕 | ✅ | ✅ 實作 | |
| 返回登入連結 | 連結 | ✅ | ✅ 實作 | |

---

### /reset-password — 重設密碼

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 新密碼輸入表單 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 確認密碼欄位 | 表單 | ✅ | ✅ 實作 | |
| 提交重設按鈕 | 按鈕 | ✅ | ✅ 實作 | |
| 返回登入連結 | 連結 | ✅ | ✅ 實作 | |

---

### /invite/setup-password — 邀請設定密碼

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 設定密碼表單 | 表單 | ✅ Feature 10（B2B 機構） | ✅ 實作 | |
| 提交按鈕 | 按鈕 | ✅ | ✅ 實作 | |

---

### /onboarding — 首次引導

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 步驟導覽進度條 | 顯示 | ✅ 15-首次登入引導.feature | ✅ 實作 | |
| 返回上一步按鈕 | 按鈕 | ✅ | ✅ 實作 | |
| 下一步/完成按鈕 | 按鈕 | ✅ | ✅ 實作 | |
| 科目選擇 | 互動 | ✅（Feature 15 有 1 個 @wip Scenario） | ✅ 實作 | |

---

### /dashboard — 使用者主控台 ⭐ 核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher（科目切換器） | 互動 | ✅ Feature 13 Rule (L40) | ✅ 實作 | |
| SubjectPickerModal（新增科目） | 互動 | ✅ Feature 13 | ✅ 實作 | |
| StreakCounter（連勝計數器） | 顯示 | ✅ Feature 13 Rule (L73) | ✅ 實作 | |
| AnnouncementBanner | 顯示 | ✅ Feature 24 | ✅ 實作 | |
| PendingJourneysBanner | 顯示 | ✅ Feature 25 | ✅ 實作 | |
| 核心指標卡（4張：考試倒數/答題數/答對率/預測及格率） | 顯示 | ✅ Feature 13 Rule (L59) | ✅ 實作 | |
| 備考模式標籤（Sprint/Standard/Mastery） | 顯示 | ✅ Feature 13 Rule (L379) | ✅ 實作 | |
| 模式說明 tooltip | 互動 | ✅ | ✅ 實作 | |
| 上傳講義（拖放 / 文件選擇） | 互動 | ✅ Feature 02 | ✅ 實作 | |
| YouTube URL 解析輸入框 + 送出 | 互動 | ✅ Feature 02 | ✅ 實作 | |
| 上傳進度條 + 狀態反饋 | 顯示 | ✅ Feature 02 | ✅ 實作 | |
| DailyQuestCard（每日任務） | 顯示 | ✅ Feature 13 Rule (L96) | ✅ 實作 | |
| 待辦提醒 activityItems | 顯示 | ✅ Feature 13 Rule (L59) | ✅ 實作 | |
| ScheduleWeekCard（排程週卡） | 顯示 | ✅ Feature 09 Rule (L130) | ✅ 實作 | |
| DomainRadarChart（領域雷達圖） | 顯示 | ✅ Feature 13 Rule (L228) | ✅ 實作 | |
| 開啟知識地圖連結 | 連結 | ✅ | ✅ 實作 | |
| 意見反饋連結 | 連結 | ✅ Feature 17 | ✅ 實作 | |
| 無科目空態 CTA | 空態 | ✅ Feature 13 | ✅ 實作 | 無 job 表查詢（合理：此空態因無科目非解析失敗） |

---

### /knowledge — 知識地圖 ⭐ 核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher（科目切換） | 互動 | ✅ Feature 03 | ✅ 實作 | |
| 左側資源列表 | 顯示 | ✅ Feature 03 | ✅ 實作 | |
| 資源刪除確認 modal | 互動 | ✅ Feature 11 | ✅ 實作 | |
| 觸發重新解析按鈕 | 按鈕 | ✅ Feature 02 | ✅ 實作 | |
| ForceGraph 視圖 | 顯示 | ✅ Feature 03b | ✅ 實作 | |
| MindMapTree 列表視圖 | 顯示 | ✅ Feature 03b Rule (L231) | ✅ 實作 | |
| Document 文件視圖 | 顯示 | ✅ Feature 03b Rule (L231) | ✅ 實作 | |
| 搜尋框（節點搜尋） | 互動 | ✅ Feature 03 | ✅ 實作 | |
| NodeDetailPanel（右側詳情面板） | 顯示 | ✅ Feature 03 | ✅ 實作 | |
| AI 教練聊天框 | 互動 | ✅ Feature 03 | ✅ 實作 | |
| 免費次數限制遮罩 | 顯示 | ✅ Feature 03 | ✅ 實作 | |
| 節點「練習」按鈕（→ /practice） | 按鈕 | ✅ Feature 32 | ✅ 實作 | |
| 節點「測驗」按鈕（→ /exam/setup） | 按鈕 | ✅ Feature 04 | ✅ 實作 | |
| 錯題熱力圖連結（→ /knowledge/wrong-answers） | 連結 | ✅ Feature 27 | ✅ 實作 | |
| 返回儀表板連結 | 連結 | ✅ | ✅ 實作 | |
| 空態（無文件）CTA | 空態 | ✅ Feature 03b | ✅ 實作 | Layer 3：有查 failure_reason ✅ (Line 243) |
| FAILED 文件 failure_reason 顯示 | 空態 | ✅ | ✅ 實作 | |

---

### /knowledge/mindmap — 知識心智圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph / MindMapTree 切換 | 互動 | ✅ Feature 03b Rule (L231) | ✅ 實作 | |
| 節點點擊 → 側邊詳情面板 | 互動 | ✅ Feature 03b | ✅ 實作 | data-testid="mindmap-node-detail-panel" |
| 節點詳情：開始練習按鈕 | 按鈕 | ✅ Feature 32 | ✅ 實作 | |
| 節點詳情：知識庫查看按鈕 | 按鈕 | ✅ Feature 03 | ✅ 實作 | |
| 空態（無節點）4 種情境 | 空態 | ✅ Feature 03b | ✅ 實作 | Layer 3 已區分四種情境 |

---

### /knowledge/wrong-answers — 個人化錯題地圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 節點掌握度熱力圖（紅/橘/綠/灰） | 顯示 | ✅ Feature 27 | ✅ 實作 | |
| 節點點擊 → 展開錯題明細（最多 5 題） | 互動 | ✅ Feature 27 | ✅ 實作 | |
| SubjectSwitcher | 互動 | ✅ Feature 27 | ✅ 實作 | |
| 返回知識地圖連結 | 連結 | ✅ | ✅ 實作 | |
| 空態（nodes.length === 0） | 空態 | 🟡 無 Job 表查詢 | 🟡 僅顯示空畫面 | 未查 resource_parse_jobs 確認空態原因 |

---

### /practice — 節點練習模式 ⭐ 核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 葉節點列表（無 nodeId 時） | 顯示 | ✅ Feature 32 | ✅ 實作 | |
| 節點選擇後題目載入 | 顯示 | ✅ Feature 32 | ✅ 實作 | |
| 答案選項 | 互動 | ✅ Feature 32 | ✅ 實作 | |
| 信心度校準（😰😐😎 三圖示） | 互動 | ✅ Feature 20 | ✅ 實作 | |
| 提交答案按鈕 | 按鈕 | ✅ Feature 32 | ✅ 實作 | |
| 下一題按鈕 | 按鈕 | ✅ Feature 32 | ✅ 實作 | |
| 回溯難度橫幅（backtrack-banner） | 顯示 | ✅ Feature 28 | ✅ 實作 | |
| 切換父節點按鈕 | 按鈕 | ✅ Feature 28 | ✅ 實作 | |
| 無題目空態（→ 前往出題 + failure_reason） | 空態 | ✅ Feature 32 | ✅ 實作 | Layer 3 已查 FAILED 文件 |
| 選擇其他節點按鈕 | 按鈕 | ✅ Feature 32 | ✅ 實作 | |
| 回知識圖譜連結 | 連結 | ✅ Feature 32 | ✅ 實作 | |

---

### /exam/setup — 測驗設定 ⭐ 核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 資源文件列表（選擇測驗範圍） | 顯示 | ✅ Feature 04 | ✅ 實作 | |
| 知識節點選擇器 | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 題數選擇（10/20/50/100） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 難度選擇（1/2/3） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 考試模式（hybrid/historical_only） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 題目排列模式（🔀交錯/📦分組/📈依難度） | 互動 | ✅ Feature 19 | ✅ 實作 | |
| 題型勾選框（multiple_choice 等） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 方案題數上限驗證警告 | 顯示 | ✅ Feature 04 | ✅ 實作 | |
| 進階出題配方（Bloom 配比，ULTRA/SUPER_ADMIN） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 中斷考試恢復提示 | 顯示 | ✅ Feature 05 | ✅ 實作 | |
| ExamLoadingOverlay（真實生成進度，後端輪詢） | 顯示 | ✅ Feature 04a | ✅ 實作 | |
| 無文件空態（→ 前往知識庫） | 空態 | ✅ Feature 04 | ✅ 實作 | |

---

### /exam/workspace — 模擬機考 ⭐ 核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Certi 打氣 Banner（5 秒後自動隱藏） | 顯示 | ✅ Feature 05 | ✅ 實作 | data-testid="certi-intro-banner" |
| 題目顯示區 | 顯示 | ✅ Feature 05 | ✅ 實作 | |
| 答案選項（單選） | 互動 | ✅ Feature 05 | ✅ 實作 | |
| 信心度校準（😰😐😎） | 互動 | ✅ Feature 20 | ✅ 實作 | |
| 計時器（紅色警示 ≤ 4:59） | 顯示 | ✅ Feature 05 | ✅ 實作 | |
| 暫停/繼續按鈕 | 按鈕 | ✅ Feature 05 | ✅ 實作 | |
| 標記待複查按鈕 | 按鈕 | ✅ Feature 05 | ✅ 實作 | |
| 題目導航網格 | 互動 | ✅ Feature 05 | ✅ 實作 | |
| 上一題/下一題按鈕 | 按鈕 | ✅ Feature 05 | ✅ 實作 | |
| 提交確認 modal | 互動 | ✅ Feature 05 | ✅ 實作 | |
| PomodoroTimer（番茄鐘） | 互動 | ✅ Feature 21 | ✅ 實作 | |
| localStorage 答題持久化 | 功能 | ✅ Feature 05 | ✅ 實作 | |

---

### /exam/results — 考試結果 ⭐ 核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 成績分數顯示 | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| Confetti 動畫（≥80% 觸發） | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| 知識點顏色標示（紅/橘/綠 ForceGraph） | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| 進入錯題本（AI 解析+教練）連結 | 連結 | ✅ Feature 06 | ✅ 實作 | |
| 逐題解析連結（→ /review?all=1） | 連結 | ✅ Feature 06 | ✅ 實作 | |
| 排列模式標籤（🔀交錯練習） | 顯示 | ✅ Feature 19 | ✅ 實作 | |
| LinkedIn 分享按鈕 | 按鈕 | ✅ Feature 06 (L143) | ✅ 實作 | |
| 下載成績卡片（html2canvas PNG） | 按鈕 | ✅ Feature 06 (L143) | ✅ 實作 | |
| 信心度四象限分析 | 顯示 | 🔴 Feature 20 Rule (L59) 要求但未實作 | 🟠 **缺失** | results/page.tsx 無任何 confidence 程式碼 |

**問題**：🔴 Feature 20 Rule「測驗結果頁應提供信心度四象限分析」含 3 個 active Scenario，但 `/exam/results/page.tsx`（459 行）完全無信心度四象限 UI

---

### /review — 錯題複習與 AI 教練 ⭐ 核心

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 題目側邊列表 | 顯示 | ✅ Feature 07 | ✅ 實作 | |
| 當前題目 + 解析 | 顯示 | ✅ Feature 07 | ✅ 實作 | |
| 引用來源切換（Citation toggle） | 互動 | ✅ Feature 07 | ✅ 實作 | |
| KaTeX 數學公式渲染 | 顯示 | ✅ Feature 07 | ✅ 實作 | |
| AI 教練聊天框 | 互動 | ✅ Feature 07 | ✅ 實作 | |
| 升級提示（FREE 用戶） | 顯示 | ✅ Feature 07 | ✅ 實作 | |
| 空態（無錯題）→ 查後端 recent-failures | 空態 | ✅ Feature 07 | ✅ 實作 | Layer 3 已實作 |

---

### /schedule — 學習記憶排程

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 排程建議列表（各科目模式/日期） | 顯示 | 🔴 Feature 09 無此頁獨立 Scenario | ✅ 實作 | |
| 「開始今日複習」按鈕（→ /exam/setup） | 連結 | 🔴 Feature 09 無 Scenario 驗證此元素 | ✅ 實作 | |
| scheduleService.getRecommendations | API | ✅ Feature 09 | ✅ 實作 | |
| 空態（recs.length === 0） | 空態 | 🔴 無 Feature 覆蓋 | 🟡 未查 Job 表 | 直接顯示「尚無備考科目可排程」 |

**問題**：
- 🔴 `/schedule` 完整功能頁面無獨立 Feature Scenario，Feature 09 僅將此路由作為連結目標
- 🟡 空態未查 resource_parse_jobs 確認原因

---

### /pricing — 定價與升級引導

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 方案比較表 | 顯示 | ✅ Feature 18（定價） | ✅ 實作 | |
| 選擇方案按鈕 | 按鈕 | ✅ Feature 18 | ✅ 實作 | |
| 免費試用 ULTRA 按鈕 | 按鈕 | ✅ Feature 18 | ✅ 實作 | |

---

### /feedback — 意見反饋

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 反饋類型選擇 | 互動 | ✅ Feature 17 | ✅ 實作 | |
| 主旨 / 內容表單 | 表單 | ✅ Feature 17 | ✅ 實作 | |
| 附件上傳 | 互動 | ✅ Feature 17 | ✅ 實作 | |
| 提交按鈕 | 按鈕 | ✅ Feature 17 | ✅ 實作 | |
| 歷史反饋列表（展開/收起） | 顯示 | ✅ Feature 17 | ✅ 實作 | |

---

### /account — 帳號設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Tab 切換（個人資料/科目/訂閱/通知） | 互動 | ✅ Feature 22 | ✅ 實作 | |
| 個人資料儲存按鈕 | 按鈕 | ✅ Feature 22 | ✅ 實作 | |
| 科目新增/移除按鈕 | 按鈕 | ✅ Feature 13 | ✅ 實作 | |
| 學習風格偏好設定 | 互動 | ✅ Feature 22 | ✅ 實作 | |
| 通知偏好（後端同步） | 互動 | ✅ Feature 22 | ✅ 實作 | |
| 訂閱管理 / 升級連結 | 互動 | ✅ Feature 08 | ✅ 實作 | |
| 帳號刪除確認 | 互動 | ✅ Feature 22 | ✅ 實作 | |

---

### /account/my-subjects — 我的科目

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目列表 | 顯示 | ✅ Feature 13 Rule (L357) | ✅ 實作 | |
| 刪除科目按鈕 | 按鈕 | ✅ Feature 13 | ✅ 實作 | |

---

### /account/weekly-reports — 每週報告

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 每週報告列表 | 顯示 | ✅ Feature 14（社群歸屬） | ✅ 實作 | |
| 生成報告按鈕 | 按鈕 | ✅ Feature 14 | ✅ 實作 | |

---

### /edu-console — B2B 機構管理後台

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| DPA 簽署 Modal | 互動 | ✅ Feature 10 (L58-65) | ✅ 實作 | |
| CSV 匯入學員 | 互動 | ✅ Feature 10 | ✅ 實作 | |
| 學員列表 | 顯示 | ✅ Feature 10 | ✅ 實作 | |
| 學員操作按鈕（移除/重設） | 按鈕 | ✅ Feature 10 | ✅ 實作 | |

---

### /edu-console/student/[id] — 學生詳情

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 學生學習進度 | 顯示 | ✅ Feature 10 | ✅ 實作 | |

---

### /resources/[id]/candidates — 考題候選管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 考題候選列表 | 顯示 | ✅ Feature 23 Rule (L132) | ✅ 實作 | |
| 審核操作按鈕 | 按鈕 | ✅ Feature 23 | ✅ 實作 | |

---

### /super-admin/* — 平台管理後台頁群

| 頁面 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|-------------|---------|------|
| /super-admin/dashboard | ✅ Feature 12 | ✅ | |
| /super-admin/users | ✅ Feature 12 | ✅ | |
| /super-admin/users/[userId] | ✅ Feature 12 Rule「用戶詳情頁」 | ✅ | |
| /super-admin/moderation | ✅ Feature 12b | ✅ | |
| /super-admin/cost-monitor | ✅ Feature 33 | ✅ | |
| /super-admin/finance | ✅ Feature 12a | ✅ | |
| /super-admin/anomaly | ✅ Feature 16 | ✅ | 含批次修復 |
| /super-admin/platform-subjects | ✅ Feature 12c Rule (L271) | ✅ | |
| /super-admin/exam-import | ✅ Feature 23 | ✅ | |
| /super-admin/prompt-templates | ✅ Feature 30 | ✅ | |
| /super-admin/prompt-templates/new | ✅ Feature 30 | ✅ | |
| /super-admin/prompt-templates/[templateId] | ✅ Feature 30 | ✅ | |
| /super-admin/retirement | ✅ Feature 25 | ✅ | |
| /super-admin/default-resources | ✅ Feature 34 | ✅ | |
| /super-admin/audit-logs | ✅ Feature 12 | ✅ | |
| /super-admin/settings | ✅ Feature 12c | ✅ | |
| /super-admin/settings/admins | ✅ Feature 12c | ✅ | |
| /super-admin/settings/announcements | ✅ Feature 24 | ✅ | |
| /super-admin/settings/api-keys | ✅ Feature 12c (L253) | ✅ | |
| /super-admin/settings/flags | ✅ Feature 12c | ✅ | |
| /super-admin/settings/plans | ✅ Feature 12c Rule (L271) | ✅ | |
| /super-admin/settings/version | ✅ Feature 12c Rule (L260) | ✅ | |

---

### /radar-demo — 雷達圖示範

純展示頁，無需 Feature 覆蓋。

---

## Feature File 覆蓋摘要

| Feature File | 概要 | @wip 數 | 對應頁面 | 備註 |
|-------------|------|---------|---------|------|
| 01-身分驗證.feature | 登入/註冊/密碼強度 | 0 | /login, /signup | |
| 02-資源上傳.feature | 上傳/版權約定 | 2 | /dashboard | |
| 03-知識心智圖.feature | 科目切換/節點聯動 | 0 | /knowledge | |
| 03a-知識心智圖生成.feature | 知識圖譜生成 | 0 | /knowledge | |
| 03b-知識心智圖導航.feature | 三視圖/AI 教練 | 0 | /knowledge, /knowledge/mindmap | |
| 04-測驗設定.feature | 設定/方案限制 | 0 | /exam/setup | |
| 04a-AI考題生成服務.feature | 生成進度 | 0 | /exam/setup | |
| 05-模擬機考.feature | 機考流程 | 0 | /exam/workspace | |
| 06-測驗結果.feature | 成績/知識點分析 | 0 | /exam/results | |
| 07-錯題複習與AI教練.feature | 複習/AI 教練 | 0 | /review | |
| 08-訂閱管理.feature | 訂閱多階層 | 0 | /account, /pricing | |
| 08a-綠界金流串接.feature | ECPay 金流 | 0 | /account | |
| 08b-付款後權限更新.feature | 付款後角色更新 | 0 | /account | |
| 09-學習記憶排程.feature | 動態排程 | 0 | /dashboard（ScheduleWeekCard），/schedule 僅為連結目標 | 🔴 /schedule 頁無獨立 Scenario |
| 10-B2B機構管理後台.feature | 機構/CSV/DPA | 0 | /edu-console | |
| 11-資源庫管理.feature | 資源連鎖清除 | 0 | /knowledge | |
| 12-平台管理後台.feature | 用戶管理/審計 | 0 | /super-admin/* | |
| 12a-平台管理後台-財務管理.feature | 財務統計 | 0 | /super-admin/finance | |
| 12b-平台管理後台-內容審核.feature | 內容審核 | 0 | /super-admin/moderation | |
| 12c-平台管理後台-系統設定.feature | Flag/配額/版本 | 0 | /super-admin/settings/* | |
| 13-個人儀表板與成就系統.feature | 儀表板/連勝 | 0 | /dashboard | |
| 14-社群歸屬與主動關懷.feature | 每週報告 | 0 | /account/weekly-reports | |
| 15-首次登入引導與學習歷程建立.feature | Onboarding | 1 @wip | /onboarding | |
| 16-異常維修管理.feature | 異常/批次修復 | 0 | /super-admin/anomaly | |
| 17-意見反饋.feature | 反饋提交 | 0 | /feedback | |
| 18-定價與升級引導.feature | 定價比較/升級 | 0 | /pricing | |
| 18-題目分類與考試趨勢分析.feature | Bloom 分佈/趨勢 | 0 | **無前端頁面** | 🔴 無對應前端視覺化頁面 |
| 19-交錯練習.feature | 交錯排列模式 | 0 | /exam/setup, /exam/results | |
| 20-信心度校準.feature | 信心度/四象限 | 0 | /exam/workspace, /practice, /exam/results | 🔴 /exam/results 四象限未實作 |
| 21-番茄鐘學習節奏.feature | 番茄計時器 | 0 | /exam/workspace | |
| 22-帳號設定與個人偏好.feature | 個人資料/通知 | 0 | /account | |
| 23-考古題題庫管理.feature | PDF 匯入/候選題 | 1 @wip | /super-admin/exam-import, /resources/[id]/candidates | |
| 24-系統公告管理.feature | 公告 CRUD | 0 | /super-admin/settings/announcements | |
| 25-AI考題退場與放榜確認.feature | 考題退場 | 0 | /super-admin/retirement | |
| 26-考綱逆向工程.feature | 考綱分析 | 0 | 後端 API only（spec L55 明確） | |
| 27-個人化錯題地圖.feature | 錯題熱力圖 | 0 | /knowledge/wrong-answers | |
| 28-階層式難度遞進.feature | 回溯難度 | 0 | /practice | |
| 29-知識樹合併對齊.feature | 知識樹合併 | 0 | 後端服務，前端呈現於 /knowledge | |
| 30-Prompt模板管理.feature | Prompt 模板 CRUD | 0 | /super-admin/prompt-templates | |
| 31-多租戶安全與資料隔離.feature | 多租戶安全 | 2 @wip | 跨頁面安全守衛 | |
| 32-節點練習模式.feature | 節點練習 | 0 | /practice | |
| 32-考古題現代化匯入.feature | 現代化 PDF 解析 | 0 | /super-admin/exam-import | |
| 33-成本監控中心.feature | AI/GCP 成本 | 0 | /super-admin/cost-monitor | |
| 34-預載科目Fork.feature | 科目 Fork | 0 | 後端 API，/super-admin/default-resources | |

---

## 問題彙整

### 🔴 Feature 缺失（需新增 Scenario）

1. **`/exam/results`** — Feature 20 Rule「後置（回應）- 測驗結果頁應提供信心度四象限分析」含 3 個 active Scenario（四象限統計表、危險盲點紅色標示、幸運猜對黃色提醒），但 `/exam/results/page.tsx`（459 行）無任何 confidence/quadrant 相關程式碼。需確認 examService.getResults() 是否已回傳四象限資料，並在結果頁補上對應 UI。（**首見：2026-05-05**）

2. **`/schedule`** — 完整排程功能頁（排程列表、各科目模式、「開始今日複習」按鈕）無獨立 Feature Scenario。Feature 09 僅在 Example L143-146 將此路由作為「前往完整排程頁」的連結目標，無 Scenario 驗證頁面元素本身。需在 Feature 09 新增 Rule「完整排程頁展示各科學習建議」並補充 Scenario。（**首見：2026-05-05**）

3. **Feature 18（題目分類與考試趨勢分析）** — 此 Feature 規格 Bloom 分佈統計、年度考試趨勢分析等前端視覺化需求，但無任何對應的前端頁面或介面入口。需確認：此 Feature 是否有計畫中的前端頁面（如 `/super-admin/exam-analytics`），或已決議僅為後端 API 功能。（**首見：2026-05-05**）

### 🟠 實作缺失（Feature 存在但頁面缺功能）

1. **`/exam/results` 信心度四象限 UI** — Feature 20 Rule (L59-83) 要求結果頁呈現：(a) 四象限統計表（confident_correct / confident_incorrect / guessing_correct / guessing_incorrect）、(b) confident_incorrect 紅色警示 + 高優先複習標記、(c) guessing_correct 黃色提醒 + AI 建議文字。`exam/results/page.tsx` 完全缺此區塊。需實作四象限元件並串接後端 confidence 統計 API。（**首見：2026-05-05**）

2. **`/knowledge/wrong-answers` 空態未查 Job 表** — `nodes.length === 0` 時直接顯示空畫面（BookOpen icon），未調用任何後端 job 表查詢。若空態原因是資源解析失敗導致無知識節點，用戶會看到空的錯題地圖而無任何指引。需加入對 `resource_parse_jobs` 或 `resourceParseService.getStatus()` 的查詢，區分「真的沒有錯題」與「解析失敗導致無節點」。（**首見：2026-05-05**）

### 🟡 空態需補強（需查 Job 表）

1. **`/schedule`** — `recs.length === 0` 空態僅顯示「尚無備考科目可排程」並引導至 /onboarding，未查詢後端 job 表確認是否有失敗的解析任務。應加入 `resource_parse_jobs` 狀態查詢，區分「無科目」與「有科目但排程/解析異常」兩種情境。（**首見：2026-05-05**）

2. **`/knowledge/wrong-answers`** — 同上述 🟠 問題 2，空態未查 job 表。（**首見：2026-05-05**）

---

## 附記：Feature Files 中 @wip 狀態彙整

| Feature File | @wip 數 | 說明 |
|-------------|---------|------|
| 02-資源上傳.feature | 2 | 版權約定進階情境（`@prd-033`） |
| 15-首次登入引導與學習歷程建立.feature | 1 | Onboarding 特定流程（`@prd-033`） |
| 23-考古題題庫管理.feature | 1 | 考古題管理進階情境（`@prd-033`） |
| 31-多租戶安全與資料隔離.feature | 2 | 多租戶隔離進階情境（`@prd-033`） |
