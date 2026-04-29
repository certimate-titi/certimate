# CertiMate Daily QA Issue Checklist
**產出時間**：2026-04-30 01:09 (Asia/Taipei)
**審查頁面數**：49 頁
**Feature File 數**：44 個
**發現問題總計**：🔴 7（新增 1）+ 🟠 5（修復確認 1）+ 🟡 4（新增 1）

---

## 頁面審查清單

### /login — 登入頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email 輸入框 | 輸入 | ✅ 01-身分驗證 | ✅ 實作 | |
| 密碼輸入框 | 輸入 | ✅ 01-身分驗證 | ✅ 實作 | |
| 密碼顯示/隱藏切換 | 按鈕 | ✅ 01-身分驗證 | ✅ 實作 | |
| 記住我勾選框 | 輸入 | ✅ 01-身分驗證 | ✅ 實作 | localStorage/sessionStorage |
| 登入按鈕 | 按鈕 | ✅ 01-身分驗證 | ✅ 實作 | |
| Google 登入按鈕 | 按鈕 | ✅ 01-身分驗證 | ✅ 實作 | |
| 忘記密碼連結 | 連結 | ✅ 01-身分驗證 | ✅ 實作 | → /forgot-password |
| 錯誤訊息區塊 | 顯示 | ✅ 01-身分驗證 | ✅ 實作 | |

---

### /signup — 註冊頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email 輸入框 | 輸入 | ✅ 01-身分驗證 | ✅ 實作 | |
| 密碼強度指示條 | 顯示 | ✅ 01-身分驗證 | ✅ 實作 | 弱/中/強 |
| 密碼顯示/隱藏 | 按鈕 | ✅ 01-身分驗證 | ✅ 實作 | |
| 同意條款勾選框 | 輸入 | ✅ 01-身分驗證 | ✅ 實作 | |
| 服務條款彈窗 | Modal | ✅ 01-身分驗證 | ✅ 實作 | |
| 隱私權政策彈窗 | Modal | ✅ 01-身分驗證 | ✅ 實作 | |
| Google SSO 按鈕 | 按鈕 | ✅ 01-身分驗證 | ✅ 實作 | |
| 送出按鈕 | 按鈕 | ✅ 01-身分驗證 | ✅ 實作 | |

---

### /onboarding — 新手引導

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 4 步驟進度條 | 顯示 | ✅ 15-首次登入引導 | ✅ 實作 | |
| SubjectPicker（科目選擇） | 互動 | ✅ 15-首次登入引導 | ✅ 實作 | |
| StepPreferences（學習偏好） | 互動 | ✅ 15-首次登入引導 | ✅ 實作 | |
| 上一步/下一步按鈕 | 按鈕 | ✅ 15-首次登入引導 | ✅ 實作 | |
| 草稿自動儲存（localStorage） | 行為 | ✅ 15-首次登入引導 | ✅ 實作 | |

---

### /dashboard — 使用者主控台（⭐ 核心頁面）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 問候標語（含用戶名） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| 備考模式標籤（Sprint/Standard/Mastery） | 顯示 | 🔴 無 Feature 覆蓋 | ✅ 實作 | 已知首見 2026-04-24 |
| 模式 Tooltip（策略說明） | 互動 | 🔴 無 Feature 覆蓋 | ✅ 實作 | 同上 |
| StreakCounter（學習連勝） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| SubjectSwitcher（科目切換） | 互動 | ✅ 13-個人儀表板 | ✅ 實作 | |
| + 新增科目按鈕 | 按鈕 | ✅ 13-個人儀表板 | ✅ 實作 | 開啟 SubjectPickerModal |
| 核心指標卡（距考日/答題數/答對率/預測及格率） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| DailyQuestCard（每日任務） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| 檔案上傳區 | 互動 | ✅ 02-資源上傳 | ✅ 實作 | 支援 PDF/Office/音訊/影片/圖片 |
| 上傳進度條（pending/processing/completed/failed） | 顯示 | ✅ 02-資源上傳 | ✅ 實作 | |
| YouTube 連結解析框 | 互動 | ✅ 02-資源上傳 | ✅ 實作 | |
| ScheduleWeekCard（週排程） | 顯示 | ✅ 09-學習記憶排程 | ✅ 實作 | |
| DomainRadarChart（領域雷達圖） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | 點擊節點導向 /knowledge |
| ActivityItems（待辦提醒） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| AnnouncementBanner（系統公告） | 顯示 | ✅ 24-系統公告管理 | ✅ 實作 | |
| PendingJourneysBanner（放榜確認） | 顯示 | ✅ 25-AI考題退場 | ✅ 實作 | |
| StudyBuddyBanner（ULTRA 共讀橫幅） | 顯示 | 🔴 無 Feature 覆蓋 | ⚠️ backend API 待建 | 已知首見 2026-04-27 |
| 意見反饋連結 | 連結 | ✅ 17-意見反饋 | ✅ 實作 | |
| 無科目時歡迎引導頁（subjectsLoaded + 空科目） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | 防止 API 未回來誤判空態 |

---

### /knowledge — 知識地圖（⭐ 核心頁面）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 互動 | ✅ 03-知識心智圖 | ✅ 實作 | |
| 資源列表（左側面板） | 顯示 | ✅ 11-資源庫管理 | ✅ 實作 | |
| FAILED 資源查 job 失敗原因 | 行為 | ✅ Layer 3 規則 | ✅ 實作 | resourceParseService.getStatus() |
| 資源解析輪詢（5s 間隔） | 行為 | ✅ 03a-知識心智圖生成 | ✅ 實作 | 直到全 COMPLETED/FAILED |
| ForceGraph 視圖 | 互動 | ✅ 03b-知識心智圖導航 | ✅ 實作 | 預設視圖 |
| MindMapTree 視圖 | 互動 | ✅ 03b-知識心智圖導航 | ✅ 實作 | |
| 視圖切換按鈕（tree/force） | 按鈕 | ✅ 03b-知識心智圖導航 | ✅ 實作 | |
| 搜尋框（過濾節點） | 輸入 | ✅ 03-知識心智圖 | ✅ 實作 | |
| 節點詳情面板（右側） | 顯示 | ✅ 03-知識心智圖 | ✅ 實作 | |
| NodeDetailPanel tab（info/material/notebook/coach） | 互動 | ✅ 03b-知識心智圖導航 | ✅ 實作 | |
| ScaffoldMaterial / ScaffoldNotebook / ScaffoldReplayCard | 顯示 | ✅ 03b-知識心智圖導航 | ✅ 實作 | |
| AI 教練聊天框（含快速提問 chips） | 互動 | ✅ 03-知識心智圖 | ✅ 實作 | |
| FREE 免費查詢次數計數器 | 顯示 | ✅ 03-知識心智圖 | ✅ 實作 | localStorage 管理 |
| + 新增資源按鈕 | 按鈕 | 🟠 Feature 存在但導向 /dashboard 而非 modal | 🟠 路徑異常 | 已知首見 2026-04-28 |
| 刪除資源確認 Modal | Modal | ✅ 03-知識心智圖 | ✅ 實作 | |
| 資源面板摺疊/展開 | 互動 | ✅ 03-知識心智圖 | ✅ 實作 | |
| 手動觸發解析按鈕 | 按鈕 | ✅ 03a-知識心智圖生成 | ✅ 實作 | |

---

### /knowledge/mindmap — 全螢幕知識地圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph/MindMapTree 視圖切換 | 互動 | ✅ 03b-知識心智圖導航 | ✅ 實作 | |
| SubjectSwitcher | 互動 | ✅ 03-知識心智圖 | ✅ 實作 | |
| 節點點擊（selectedNodeId） | 互動 | ✅ 03b-知識心智圖導航 | ✅ 實作 | |
| 返回按鈕 | 按鈕 | ✅ 03b | ✅ 實作 | |

---

### /exam/setup — 測驗設定（⭐ 核心頁面）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| 文件選擇列表（僅 COMPLETED） | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| 系統知識節點選擇 | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| 題數選擇（依方案上限截斷） | 互動 | ✅ 04-測驗設定 | ✅ 實作 | FREE:10 / PRO:50 / ULTRA:∞ |
| 難度選擇（1/2/3） | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| 題目排列模式（交錯/分組/依難度） | 互動 | ✅ 19-交錯練習 | ✅ 實作 | orderMode state 確認存在 |
| 題型選擇 | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| 考試模式（hybrid/historical_only） | 互動 | ✅ 04-測驗設定 | ✅ 實作 | |
| Bloom 自訂比例（Admin 限定） | 互動 | ✅ 18-題目分類 | ✅ 實作 | |
| 中斷考試恢復提示 | 顯示 | ✅ 05-模擬機考 | ✅ 實作 | |
| 出題 Loading Overlay | 顯示 | ✅ 04a-AI考題生成服務 | ✅ 實作 | 6 階段動畫 |

---

### /exam/workspace — 模擬考作答（⭐ 核心頁面）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 題目顯示 | 顯示 | ✅ 05-模擬機考 | ✅ 實作 | |
| 選項按鈕（A/B/C/D） | 按鈕 | ✅ 05-模擬機考 | ✅ 實作 | |
| 倒數計時器（localStorage 持久化） | 顯示 | ✅ 05-模擬機考 | ✅ 實作 | |
| PomodoroTimer（番茄鐘） | 互動 | ✅ 21-番茄鐘 | ✅ 實作 | line 226 確認渲染 |
| 標記題目按鈕（Flag） | 按鈕 | ✅ 05-模擬機考 | ✅ 實作 | |
| 暫停/繼續按鈕 | 按鈕 | ✅ 05-模擬機考 | ✅ 實作 | |
| 題目導覽網格（LayoutGrid） | 互動 | ✅ 05-模擬機考 | ✅ 實作 | |
| 提交考試確認 Dialog | Modal | ✅ 05-模擬機考 | ✅ 實作 | |
| 頁面離開警告（beforeunload） | 行為 | ✅ 05-模擬機考 | ✅ 實作 | |
| AI 教練 Certi 打氣介面 | 顯示 | 🔴 Feature 05 有 Scenario，頁面無實作 | 🔴 缺失 | 已知首見 2026-04-29 |

**問題**：Feature 05 Rule「AI 教練在開始測驗時提供專屬打氣訊息（Certi 角色）」在頁面完全缺失，無任何相關 state 或 component。

---

### /exam/results — 測驗結果（⭐ 核心頁面）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 分數卡片（得分/及格狀態/門檻） | 顯示 | ✅ 06-測驗結果 | ✅ 實作 | |
| 與上次比較（+/-分差） | 顯示 | ✅ 06-測驗結果 | ✅ 實作 | |
| Confetti 動畫（>=80 分） | 顯示 | ✅ 06-測驗結果 | ✅ 實作 | |
| 答對/答錯/未答統計 | 顯示 | ✅ 06-測驗結果 | ✅ 實作 | |
| 知識節點三色標示（>=80%綠/60-79%橘/<60%紅） | 顯示 | ✅ 06-測驗結果 | ✅ 實作 | |
| ForceGraph 知識圖譜 | 顯示 | ✅ 06-測驗結果 | ✅ 實作 | |
| AI 摘要（aiSummary） | 顯示 | ✅ 06-測驗結果 | ✅ 實作 | |
| Bloom 分佈（bloomBreakdown） | 顯示 | ✅ 18-題目分類 | ✅ 實作 | |
| 連續退步 AI 教練介入橫幅 | 顯示 | ✅ 07-錯題複習 | ✅ 實作 | consecutiveDeclines >= 2 |
| 逐題解析連結 → /review | 連結 | ✅ 06/07 | ✅ 實作 | line 241 確認 |
| 分享至 LinkedIn 按鈕 | 按鈕 | 🔴 無 Feature Scenario 覆蓋 | ✅ 實作 | 已知首見 2026-04-24 |
| 下載成績圖卡（html2canvas） | 按鈕 | 🔴 無 Feature Scenario 覆蓋 | ✅ 已實作（html2canvas@1.4.1） | 舊 stub 標記應改為已修復 |

**備註**：舊 ToDoList 標記下載為「alert stub」，但程式碼已改用 html2canvas，html2canvas@1.4.1 已在 package.json 確認安裝，屬已修復狀態。

---

### /practice — 自由練習（⭐ 核心頁面）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 互動 | ✅ 32-節點練習 | ✅ 實作 | |
| 知識節點樹列表 | 顯示 | ✅ 32-節點練習 | ✅ 實作 | |
| 選題後進入答題 | 互動 | ✅ 32-節點練習 | ✅ 實作 | |
| 選擇答案 + 送出 | 互動 | ✅ 32-節點練習 | ✅ 實作 | |
| 即時回饋（正確/錯誤 + 詳解） | 顯示 | ✅ 32-節點練習 | ✅ 實作 | |
| 信心度校準（blindInferenceService） | 互動 | ✅ 20-信心度校準 | ✅ 實作 | |
| 下一題 / 回選題 | 按鈕 | ✅ 32-節點練習 | ✅ 實作 | |
| no-questions 空態文字提示 | 顯示 | ✅ 32-節點練習 | 🟡 未查 resource_parse_jobs | 已知首見 2026-04-24 |
| 空態「前往出題」按鈕 | 按鈕 | ✅ 32-節點練習 | ✅ 實作 | |
| 空態「回知識圖譜」按鈕 | 按鈕 | ✅ 32-節點練習 | ✅ 實作 | |

**問題**：no-questions 空態未呼叫 resourceParseService.getStatus() 查詢 failure_reason，違反 Layer 3 規則。

---

### /review — 錯題複習與 AI 教練（⭐ 核心頁面）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 互動 | ✅ 07-錯題複習 | ✅ 實作 | |
| 錯題側欄列表 | 顯示 | ✅ 07-錯題複習 | ✅ 實作 | |
| 題目詳情（正確/錯誤選項對比） | 顯示 | ✅ 07-錯題複習 | ✅ 實作 | |
| 引用來源顯示 | 顯示 | ✅ 07-錯題複習 | ✅ 實作 | |
| MathContent 數學公式渲染 | 顯示 | 🟠 Feature 07 無 Scenario，KaTeX 是否實際渲染待確認 | 🟠 不確定 | 已知首見 2026-04-28 |
| AI 教練聊天框（PRO+） | 互動 | ✅ 07-錯題複習 | ✅ 實作 | |
| 毛玻璃付費牆（FREE 用戶） | 顯示 | ✅ 07-錯題複習 | ✅ 實作 | |
| 空態「全部答對！」 | 顯示 | ✅ 07-錯題複習 | 🟡 未查 exam_generation_jobs | 已知首見 2026-04-28 |

**問題**：空態未查詢 job 表確認是否為 job FAILED 所致（Layer 3）；MathContent KaTeX 渲染行為需 Playwright E2E 驗證。

---

### /schedule — 學習排程

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目排程卡片列表 | 顯示 | ✅ 09-學習記憶排程 | ✅ 實作 | |
| 學習模式標籤（Sprint/Standard/Mastery） | 顯示 | ✅ 09-學習記憶排程 | ✅ 實作 | |
| 待複習題數 / 推薦題數 | 顯示 | ✅ 09-學習記憶排程 | ✅ 實作 | |
| 開始今日複習按鈕 | 按鈕 | ✅ 09-學習記憶排程 | ✅ 實作 | → /exam/setup |
| 空態（recs.length === 0） | 顯示 | 🟡 未查 schedule job 失敗原因 | 🟡 僅顯示「尚無備考科目」 | 已知首見 2026-04-29 |

---

### /pricing — 定價頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| FREE 方案卡片 | 顯示 | ✅ 18-定價與升級引導 | ✅ 實作 | |
| PRO_199 方案卡片 | 顯示 | ✅ 18-定價與升級引導 | ✅ 實作 | |
| PRO_PLUS_399 方案卡片 | 顯示 | ✅ 18-定價與升級引導 | 🔴 「進階 AI 教練: false」與 Feature 03 規格不符 | 新增 2026-04-30 |
| ULTRA_1599 方案卡片 | 顯示 | ✅ 18-定價與升級引導 | ✅ 實作 | 進階 AI 教練: true |
| 升級按鈕（ECPay） | 按鈕 | ✅ 08a-綠界金流 | ✅ 實作 | |

**問題**：PRO_PLUS_399 功能矩陣中「進階 AI 教練」顯示 `false`，但 Feature 03 明定 PRO_PLUS_399 可使用完整 AI 教練（含深度策略分析、後端切換 Claude 3.5 Sonnet）。定價頁說明與規格不一致，可能誤導用戶升級決策。

---

### /feedback — 意見反饋

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 回饋類型選擇（BUG/功能建議/勘誤/其他） | 互動 | ✅ 17-意見反饋 | ✅ 實作 | |
| 主旨 / 內容輸入框 | 輸入 | ✅ 17-意見反饋 | ✅ 實作 | |
| 截圖上傳（最多 3 張，5MB 限制） | 互動 | ✅ 17-意見反饋 | ✅ 實作 | |
| 送出按鈕 | 按鈕 | ✅ 17-意見反饋 | ✅ 實作 | |
| 過往回饋紀錄列表（含管理員回覆） | 顯示 | ✅ 17-意見反饋 | ✅ 實作 | |

---

### /account — 個人帳號設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Tab 切換（profile/billing/security/preferences/achievements） | 互動 | ✅ 22-帳號設定 | ✅ 實作 | |
| 個人資料編輯 | 互動 | ✅ 22-帳號設定 | ✅ 實作 | |
| 密碼修改 | 互動 | ✅ 01-身分驗證 | ✅ 實作 | |
| 帳號刪除確認 Modal | Modal | ✅ 01-身分驗證 | ✅ 實作 | |
| 訂閱與帳單資訊 | 顯示 | ✅ 08-訂閱管理 | ✅ 實作 | |
| AchievementGrid（成就系統） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| GrowthTimeline（成長時間軸） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| 通知偏好設定（localStorage 存儲） | 互動 | 🟠 Feature 22 未涵蓋 localStorage 偏好持久化 | ✅ 實作（localStorage）| 觀察中 |

---

### /account/my-subjects — 我的自建考科

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 自建考科列表 | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| 刪除科目確認 | 互動 | ✅ 13-個人儀表板 | ✅ 實作 | |
| 空態（無自建考科） | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | 空態不涉及 job 表，無 Layer 3 問題 |

---

### /account/weekly-reports — 歷史週報

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 週報列表（學習時數/測驗/答題量/AI摘要） | 顯示 | ✅ 14-社群歸屬與主動關懷 | ✅ 實作 | |
| 產生本週報告按鈕（手動觸發 cron） | 按鈕 | ✅ 14-社群歸屬 | ✅ 實作 | |
| 空態（reports.length === 0） | 顯示 | 🟡 未查週報 job 失敗原因 | 🟡 僅顯示「尚無週報」 | 新增 2026-04-30 |

**問題**：空態未查詢週報產生 job 狀態，無法區分「真正無週報」vs「cron job 失敗未產生」（Layer 3 違規）。

---

### /edu-console — B2B 機構主控台

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 學生名單列表 | 顯示 | ✅ 10-B2B機構管理 | ✅ 實作 | |
| 搜尋框 | 輸入 | ✅ 10-B2B機構管理 | ✅ 實作 | |
| CSV 批次匯入 Modal | Modal | ✅ 10-B2B機構管理 | ✅ 實作 | |
| 下載 CSV 範本按鈕 | 按鈕 | ✅ 10-B2B機構管理 | ✅ 實作 | |
| 學生進度 CompetencyBar | 顯示 | ✅ 10-B2B機構管理 | ✅ 實作 | |
| StatusBadge（活躍/需關注/未啟用） | 顯示 | ✅ 10-B2B機構管理 | ✅ 實作 | |

---

### /resources/[id]/candidates — 題目候選審核

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 候選題目審核 UI | 互動 | ✅ 23-考古題題庫管理 | 🔴 page.tsx 為靜態 stub，完整邏輯在 client.tsx | 已知首見 2026-04-27 |

---

### /super-admin 頁面群

| 頁面 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|-------------|---------|------|
| /super-admin/dashboard | ✅ 12-平台管理後台 | ✅ KPI 卡片 + Recharts 趨勢圖 | |
| /super-admin/users | ✅ 12-平台管理後台 | ✅ 搜尋/篩選/停權/匯出 CSV | |
| /super-admin/users/[userId] | ✅ 12-平台管理後台 | ✅ 詳情 + 停權 + 通知 | |
| /super-admin/platform-subjects | 🔴 **無任何 Feature 覆蓋** | ✅ 實作 | 已知首見 2026-04-27 |
| /super-admin/cost-monitor | ✅ 33-成本監控中心 | ✅ AI API 成本 + 預算 + 趨勢 | |
| /super-admin/anomaly | ✅ 16-異常維修管理 | 🟠 批次修復 UI 缺失 | 已知首見 2026-04-24 |
| /super-admin/audit-logs | ✅ 12-平台管理後台 | ✅ | |
| /super-admin/moderation | ✅ 12b-內容審核 | ✅ | |
| /super-admin/retirement | ✅ 25-AI考題退場 | ✅ | |
| /super-admin/exam-import | ✅ 23-考古題題庫管理 | ✅ | |
| /super-admin/default-resources | ✅ 34-預載科目Fork | ✅ | |
| /super-admin/finance | ✅ 12a-財務管理 | ✅ | |
| /super-admin/prompt-templates（列表/編輯/new） | ✅ 30-Prompt模板管理 | ✅ 含 A/B 測試 | |
| /super-admin/settings | ✅ 12c | ✅ AI 模型路由 | |
| /super-admin/settings/plans | ✅ 12c | ✅ | |
| /super-admin/settings/announcements | ✅ 24 | ✅ | |
| /super-admin/settings/flags | ✅ 12c | ✅ | |
| /super-admin/settings/admins | ✅ 12c | ✅ | |
| /super-admin/settings/api-keys | ✅ 12c | ✅ | |
| /super-admin/settings/version | ✅ 12c | ✅ | |

---

### 驗證/密碼流程頁面群

| 頁面 | Feature 覆蓋 | 實作狀態 |
|------|-------------|---------|
| /verify-email | ✅ 01-身分驗證 | ✅ |
| /verify-email/sent（含重寄 60s 冷卻） | ✅ 01-身分驗證 | ✅ 修復（resend error 顯示，2026-04-29）|
| /forgot-password | ✅ 01-身分驗證 | ✅ |
| /reset-password | ✅ 01-身分驗證 | ✅ |
| /invite/setup-password（EDU 學生邀請啟用） | ✅ 01-身分驗證 | ✅ |

---

### 其他頁面

| 頁面 | Feature 覆蓋 | 備註 |
|------|-------------|------|
| /（root） | 無特定 Feature | 登入後導向 /dashboard |
| /radar-demo | 無特定 Feature | Demo 頁，非核心功能 |

---

## Feature File 覆蓋摘要

| Feature File | 涵蓋主要功能 | 特殊 Tag | 狀態 |
|-------------|------------|---------|------|
| 01-身分驗證 | 登入/註冊/Google SSO/密碼/EDU邀請 | 3 @manual | ✅ |
| 02-資源上傳 | 文件上傳/YouTube/版權約定 | 2 @wip | ⚠️ |
| 03-知識心智圖 | 跨學科導航/AI教練/商業漏斗 | 0 | ✅ |
| 03a-知識心智圖生成 | 解析觸發/輪詢 | 0 | ✅ |
| 03b-知識心智圖導航 | 視圖切換/節點操作 | 0 | ✅ |
| 04-測驗設定 | 科目/節點/題數/難度 | 0 | ✅ |
| 04a-AI考題生成服務 | AI 出題流程 | 0 | ✅ |
| 05-模擬機考 | 作答/計時/標記/提交 | 0 | ✅ |
| 06-測驗結果 | 成績/節點三色/比較 | 0 | ✅ |
| 07-錯題複習與AI教練 | 錯題列表/AI教練/付費牆 | 2 @playwright-e2e | ✅ |
| 08-訂閱管理 | 方案切換/ECPay/EDU衝突 | 0 | ✅ |
| 09-學習記憶排程 | Sprint/Standard/Mastery 排程 | 0 | ✅ |
| 10-B2B機構管理後台 | 學生管理/CSV/邀請 | 0 | ✅ |
| 11-資源庫管理 | 資源CRUD/刪除防呆 | 無 @frontend | ✅ |
| 12-平台管理後台 | Super Admin 核心功能 | 0 | ✅ |
| 13-個人儀表板與成就系統 | 儀表板/科目切換/成就 | 0 | ✅ |
| 14-社群歸屬與主動關懷 | 週報/共讀 | 0 | ✅ |
| 15-首次登入引導 | Onboarding 流程 | 1 @wip | ⚠️ |
| 16-異常維修管理 | 異常偵測/批次修復 | 0 | ✅ |
| 17-意見反饋 | 回饋提交/管理員回覆 | 0 | ✅ |
| 18-定價與升級引導 | 方案說明/升級 CTA | 0 | ✅ |
| 18-題目分類與考試趨勢分析 | Bloom 六層/趨勢圖 | 0 | ✅ |
| 19-交錯練習 | interleaved/grouped/sequential | 0 | ✅ |
| 20-信心度校準 | 盲推理/信心校準 | 2 @ignore | ⚠️ |
| 21-番茄鐘學習節奏 | PomodoroTimer | 0 | ✅ |
| 22-帳號設定與個人偏好 | Profile/通知/主題 | 0 | ✅ |
| 23-考古題題庫管理 | 題目審核/採納/退回 | 1 @wip | ⚠️ |
| 24-系統公告管理 | 公告 CRUD | 0 | ✅ |
| 25-AI考題退場與放榜確認 | 考題退場/放榜 | 0 | ✅ |
| 26-考綱逆向工程 | 考綱分析 | 0 | ✅ |
| 27-個人化錯題地圖 | 錯題視覺化 | 0 | ✅ |
| 28-階層式難度遞進 | 難度自適應 | 0 | ✅ |
| 29-知識樹合併對齊 | 知識樹合併 | 0 | ✅ |
| 30-Prompt模板管理 | 版本控制/A/B測試 | 0 | ✅ |
| 31-多租戶安全與資料隔離 | RLS/租戶隔離 | 2 @wip | ⚠️ |
| 32-節點練習模式 | 節點作答/進度 | 0 | ✅ |
| 32-考古題現代化匯入 | 題庫匯入 | 0 | ✅ |
| 33-成本監控中心 | AI成本/預算告警 | 0 | ✅ |
| 34-預載科目Fork | 科目 Fork/冪等/原子性 | 0 | ✅ |

---

## 問題彙整

### 🔴 Feature 缺失（需新增 Gherkin Scenario）

1. `/dashboard` — 備考模式標籤（Sprint/Standard/Mastery）及模式 Tooltip 無任何 Feature Scenario 覆蓋（首見：2026-04-24）
2. `/exam/results` — [分享至 LinkedIn] 按鈕無 Feature Scenario 覆蓋（首見：2026-04-24）
3. `/exam/results` — [下載圖卡] 功能已由 html2canvas 實作，但仍無 Feature Scenario 覆蓋（首見：2026-04-24）
4. `/dashboard` — StudyBuddyBanner（ULTRA 共讀橫幅）無任何 Feature 覆蓋（首見：2026-04-27）
5. `/super-admin/platform-subjects` — 平台科目管理整頁無任何 Feature 覆蓋（首見：2026-04-27）
6. `/exam/workspace` — Feature 05 Scenario「AI 教練 Certi 打氣介面」在頁面完全無對應實作（首見：2026-04-29）
7. **🆕 `/pricing`** — PRO_PLUS_399 功能矩陣「進階 AI 教練」顯示 false，與 Feature 03 明定 PRO_PLUS_399 可用完整 AI 教練（含 Claude 3.5 Sonnet）相違背（首見：**2026-04-30**）

### 🟠 實作缺失（Feature 存在但頁面缺功能或實作異常）

1. `/super-admin/anomaly` — Feature 16「批次修復」缺乏對應 UI 元素與 Scenario（首見：2026-04-24）
2. `/review` — MathContent KaTeX 渲染邏輯未確認，Feature 07 無對應 Scenario（首見：2026-04-28）
3. `/knowledge` — 「+ 新增資源」按鈕點擊後導向 `/dashboard` 而非直接開啟上傳 Modal，Feature 03 無此路徑 Scenario（首見：2026-04-28）
4. `/resources/[id]/candidates` — Feature 23 有 Scenario，但前端 page.tsx 為靜態 stub，完整功能在 client.tsx，需確認 UI 完整性（首見：2026-04-27）
5. **✅ 修復確認** `/exam/results` — 下載圖卡已由 html2canvas@1.4.1 實作，ToDoList 舊條目「alert stub」應標記 [x]（確認：2026-04-30）

### 🟡 空態補強（需查 Job 表）

1. `/practice` — no-questions 空態未呼叫 resourceParseService.getStatus() 取得 failure_reason（首見：2026-04-24）
2. `/review` — `wrongQuestions.length === 0` 空態未查詢 `exam_generation_jobs` / `resource_parse_jobs`（首見：2026-04-28）
3. `/schedule` — `recs.length === 0` 空態未查詢 schedule 相關 job 表（首見：2026-04-29）
4. **🆕 `/account/weekly-reports`** — `reports.length === 0` 空態顯示「尚無週報」，未查詢週報產生 job 失敗原因（首見：**2026-04-30**）
