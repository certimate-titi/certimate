# CertiMate Daily QA Issue Checklist
**產出時間**：2026-04-29 01:09 (Asia/Taipei)
**審查頁面數**：49 頁
**Feature File 數**：44 個
**發現問題總計**：🔴 1 新增 ｜ 🟠 1 新增 ｜ 🟡 2 新增 ｜ ✅ 2 項舊問題確認已解決

---

## 核心五頁審查

### /dashboard — 使用者主控台

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher 科目切換器 | 互動 | ✅ Feature 13 | ✅ 實作 | |
| StreakCounter 連勝計數 | 顯示 | ✅ Feature 13 | ✅ 實作 | |
| DailyQuestCard 每日任務 | 顯示 | ✅ Feature 13 | ✅ 實作 | |
| 備考模式標籤（Sprint/Standard/Mastery） | 顯示+互動 | 🔴 無對應 Feature | ✅ 實作 | tooltip 展開功能，Feature 未覆蓋 |
| 核心指標卡（倒數/答題數/答對率/預測及格率） | 顯示 | ✅ Feature 13 | ✅ 實作 | |
| 上傳檔案按鈕 | 互動 | ✅ Feature 02 | ✅ 實作 | |
| YouTube URL 輸入+解析 | 互動 | ✅ Feature 02 | ✅ 實作 | |
| DomainRadarChart 雷達圖 | 顯示 | ✅ Feature 13 | ✅ 實作 | |
| AnnouncementBanner 公告橫幅 | 顯示 | ✅ Feature 24 | ✅ 實作 | |
| PendingJourneysBanner 待確認旅程 | 顯示 | ✅ Feature 25 | ✅ 實作 | |
| ActivityItems 待辦提醒 | 顯示 | ✅ Feature 13 | ✅ 實作 | |
| StudyBuddyBanner（ULTRA 共讀橫幅） | 顯示 | 🔴 無對應 Feature | ⚠️ 程式碼僅有註解（未渲染） | |
| SubjectPickerModal 新增科目 | 互動 | ✅ Feature 13 | ✅ 實作 | |
| ScheduleWeekCard 排程週卡 | 顯示 | ✅ Feature 09 | ✅ 實作 | |
| 空態（無科目）提示+「開始選擇科目」 | 空態 | ✅ Feature 15 | ✅ 實作 | |
| 意見反饋連結 | 連結 | ✅ Feature 17 | ✅ 實作 | |

**問題**：備考模式標籤及 StudyBuddyBanner 無 Feature 覆蓋（已登錄 ToDoList）

---

### /knowledge — 知識地圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher 科目切換 | 互動 | ✅ Feature 03b | ✅ 實作 | |
| MindMapTree 心智圖列表 | 顯示 | ✅ Feature 03 | ✅ 實作 | |
| ForceGraph 動態圖譜 | 顯示 | ✅ Feature 03 | ✅ 實作 | |
| NodeDetailPanel 節點詳情面板 | 顯示 | ✅ Feature 03b | ✅ 實作 | |
| 搜尋知識點 | 互動 | ✅ Feature 03b | ✅ 實作 | |
| 資源列表（左側欄） | 顯示 | ✅ Feature 11 | ✅ 實作 | |
| 刪除文件確認 Modal | 互動 | ✅ Feature 03b | ✅ 實作 | |
| AI 教練對話框 | 互動 | ✅ Feature 03b | ✅ 實作 | |
| AI 聊天快速提問 Chips | 互動 | ✅ Feature 03b | ✅ 實作（3 個 chips） | |
| FREE 使用者剩餘查詢次數（`剩 x/3`） | 顯示 | ✅ Feature 03b | ✅ 實作（line 992） | |
| 毛玻璃鎖定（額度用盡） | 顯示 | ✅ Feature 03b | ✅ 實作 | |
| YouTube 嵌入播放器 | 互動 | ✅ Feature 03b | ✅ 實作 | |
| 觸發 LLM 解析按鈕 | 互動 | ✅ Feature 03a | ✅ 實作 | |
| ScaffoldMaterial / ScaffoldNotebook | 顯示 | ✅ Feature 03 | ✅ 實作 | |
| 空態（無資源上傳） | 空態 | ✅ Feature 03 | ✅ 實作 | 含 FAILED 狀態分類 |
| 「+ 新增資源」按鈕 → 導向 /dashboard | 互動 | 🟠 Feature 03 無覆蓋此導航路徑 | ⚠️ 導向 /dashboard 而非開 modal | 已登錄 ToDoList |

**問題**：「新增資源」跨頁導航行為無 Feature 保護（已登錄）

---

### /knowledge/mindmap — 完整知識心智圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph 動態圖譜視圖 | 顯示 | 🔴 無對應 Scenario | ✅ 實作 | |
| MindMapTree 列表視圖 | 顯示 | 🔴 無對應 Scenario | ✅ 實作 | |
| 視圖切換（動態圖譜↔列表模式） | 互動 | 🔴 無對應 Scenario | ✅ 實作 | 已登錄 ToDoList |
| SubjectSwitcher | 互動 | ✅ Feature 03 | ✅ 實作 | |
| 節點選取 + 高亮 | 互動 | ✅ Feature 03b | ✅ 實作 | |
| 返回知識地圖連結 | 連結 | — | ✅ 實作 | |
| 空態（無節點） | 空態 | ✅ Feature 03a | ✅ 實作（4 種情境區分） | [x] 已解決 |

**問題**：ForceGraph/MindMapTree 視圖切換無 Feature Scenario（已登錄 ToDoList）

---

### /exam/setup — 測驗設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 資源文件選擇（Checkbox） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 考古題節點選擇（全選/取消） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 出題模式（AI 混合 / 考古題） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| **題目排列模式（交錯/分組/依難度）** | 互動 | ✅ Feature 19 | ✅ **確認已實作**（2026-04-29） | 先前 ToDoList 標為未實作，今日確認已修正 |
| 題數選擇（10/20/50/100） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 難度滑桿 | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 題型偏好（單選/填空/計算） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 進階出題配方（Admin only） | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 方案題數上限鎖定（Lock icon） | 顯示 | ✅ Feature 04 | ✅ 實作 | |
| SubjectSwitcher | 互動 | ✅ Feature 04 | ✅ 實作 | |
| 空態（無資源） | 空態 | ✅ Feature 04 | ✅ 實作（含引導至知識庫） | |
| 「生成專屬模擬考」按鈕 | 互動 | ✅ Feature 04 | ✅ 實作 | |
| ExamLoadingOverlay 生成動畫 | 顯示 | ✅ Feature 04a | ✅ 實作 | |

**✅ 確認已解決**：Feature 19 排列模式 `orderMode` 已實作為三按鈕 UI（🔀 交錯 / 📦 分組 / 📈 依難度）

---

### /exam/workspace — 模擬考作答

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 題目顯示（選項 A-D） | 顯示 | ✅ Feature 05 | ✅ 實作 | |
| 倒數計時器 | 顯示 | ✅ Feature 05 | ✅ 實作 | |
| **PomodoroTimer 番茄鐘** | 互動 | ✅ Feature 21 | ✅ **確認已渲染**（line 226） | 先前 ToDoList 標為待確認，今日確認 |
| 標記複查（旗幟） | 互動 | ✅ Feature 05 | ✅ 實作 | |
| 暫停/繼續 | 互動 | ✅ Feature 05 | ✅ 實作 | |
| 題目導航網格 | 互動 | ✅ Feature 05 | ✅ 實作 | |
| 交卷確認彈窗（未答題數提示） | 互動 | ✅ Feature 05 | ✅ 實作 | |
| localStorage 中斷續答 | 功能 | ✅ Feature 05 | ✅ 實作 | |
| beforeunload 警告 | 功能 | ✅ Feature 05 | ✅ 實作 | |
| AI 教練打氣介面（Certi / 開場動畫） | 顯示 | ✅ Feature 05 | 🔴 **未實作** | Feature 05 Scenario 明確要求，頁面無此 UI |
| 空態/錯誤態（無考題） | 空態 | ✅ Feature 05 | ✅ 實作 | |

**🔴 本次新發現**：Feature 05 Scenario「開始測驗前 AI 基於使用者狀態動態生成打氣語句，顯示 AI 教練角色（Certi）打氣介面」，頁面程式碼中無任何對應 UI 實作

---

### /exam/results — 測驗結果

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 得分卡（分數/合格/鼓勵語） | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| 與上次比較（+/- 分數） | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| 答對/答錯/未答統計 | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| 完賽數據（時間/平均/標記題） | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| Confetti 動畫（及格時） | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| 知識節點分析（顏色標示） | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| AI Coach 介入（連續退步） | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| Bloom 分析區塊 | 顯示 | ✅ Feature 18 | ✅ 實作 | |
| ForceGraph 知識節點視覺化 | 顯示 | ✅ Feature 06 | ✅ 實作 | |
| 逐題解析入口（「查看解析」按鈕） | 互動 | ✅ Feature 06 | 🟠 **未實作** | 已登錄 ToDoList |
| 成績卡片下載按鈕 | 互動 | 🔴 無 Feature Scenario | 🟠 **stub** | 已登錄 ToDoList |
| 「重新測驗」連結 | 連結 | ✅ Feature 06 | ✅ 實作 | |
| 「前往錯題複習」連結 | 連結 | ✅ Feature 07 | ✅ 實作 | |

---

### /practice — 自由練習

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 知識節點選擇列表 | 顯示 | ✅ Feature 32 | ✅ 實作 | |
| 題目作答介面 | 互動 | ✅ Feature 32 | ✅ 實作 | |
| 即時回饋（正解/詳解） | 顯示 | ✅ Feature 32 | ✅ 實作 | |
| blindInferenceService 信心度校準 | 功能 | ✅ Feature 20 | ✅ 實作 | |
| SubjectSwitcher | 互動 | ✅ Feature 32 | ✅ 實作 | |
| 空態（無題目） | 空態 | ✅ Feature 32 | 🟡 有提示但**未查 resource_parse_jobs** | 已登錄 ToDoList |
| 「前往出題」快捷按鈕（空態） | 互動 | ✅ Feature 32 | ✅ 實作 | |
| 「回知識圖譜」按鈕（空態） | 互動 | ✅ Feature 32 | ✅ 實作 | |

---

### /review — 錯題複習與 AI 教練

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 錯題列表側邊欄 | 顯示 | ✅ Feature 07 | ✅ 實作 | |
| 題目詳情（題幹/選項/正解） | 顯示 | ✅ Feature 07 | ✅ 實作 | |
| MathContent 公式渲染 | 顯示 | ✅ Feature 07 | ✅ 實作（MathContent component） | |
| KaTeX disclaimer 標示 | 顯示 | 🟠 Feature 07 無 Scenario | ✅ UI 顯示 | MathContent 包裝 KaTeX，直接 import 待確認 |
| AI 教練對話框 | 互動 | ✅ Feature 07 | ✅ 實作（PRO+ 限定） | |
| FREE 毛玻璃遮罩 | 顯示 | ✅ Feature 07 | ✅ 實作 | |
| SubjectSwitcher | 互動 | ✅ Feature 07 | ✅ 實作 | |
| 空態（「全部答對！」） | 空態 | ✅ Feature 07 | 🟡 **未查 job 表** | Layer 3 違規，已登錄 ToDoList |
| 引用來源切換（showCitation） | 互動 | ✅ Feature 07 | ✅ 實作 | |

---

## 其他頁面審查（簡報）

| 頁面 | 主要元素 | Feature 覆蓋 | 狀態 |
|------|---------|-------------|------|
| /login | Email/密碼/Google SSO/記住我/密碼顯示切換/錯誤訊息 | ✅ Feature 01 | 正常 |
| /signup | 服務條款/密碼強度/Email 驗證 | ✅ Feature 01 | 需 E2E 驗證 |
| /verify-email/sent | 60 秒冷卻重寄按鈕 | ✅ Feature 01 | 🟡 resend 失敗 silent（新發現） |
| /invite/setup-password | 密碼設定/token 驗證 | ✅ Feature 01 | 正常 |
| /onboarding | 四步驟（Welcome→SubjectPicker→Preferences→Confirmation） | ✅ Feature 15 | 正常 |
| /schedule | Sprint/Standard/Mastery 模式卡/「開始今日複習」 | ✅ Feature 09 | 🟡 空態未查 job（新發現） |
| /account | 5 Tab（個人/訂閱/安全/偏好/成就） | ✅ Feature 22 | 正常 |
| /account/weekly-reports | 週報列表/手動觸發 | ✅ Feature 14 | 正常 |
| /account/my-subjects | 自建科目/刪除 | ✅ Feature 13 | 正常 |
| /pricing | 四方案對照/ECPay 結帳 | ✅ Feature 18 | 正常 |
| /feedback | 四類型/截圖上傳/歷史回饋 | ✅ Feature 17 | 正常 |
| /edu-console | CSV 匯入/學員管理 | ✅ Feature 10 | 正常 |
| /super-admin/dashboard | 儀表板統計 | ✅ Feature 12 | 正常 |
| /super-admin/users | 使用者列表/停權 | ✅ Feature 12 | 正常 |
| /super-admin/prompt-templates | CRUD/版本/A/B 測試 | ✅ Feature 30 | 正常 |
| /super-admin/settings/version | 版本資訊 | 🔴 無 Feature | 已登錄 |
| /super-admin/platform-subjects | 平台科目管理 | 🔴 無 Feature | 已登錄 |
| /resources/[id]/candidates | 候選考題管理 | 🔴 無 Feature | 已登錄 |
| /super-admin/anomaly | 異常維修 | ⚠️ 批次修復 UI 缺失 | 已登錄 |

---

## 問題彙整

### 🔴 Feature 缺失（需新增 Scenario）

1. `/dashboard` — 備考模式標籤 Sprint/Standard/Mastery Tooltip 無 Feature Scenario（首見：2026-04-24）
2. `/dashboard` — StudyBuddyBanner（ULTRA 共讀計數）無 Feature Scenario（首見：2026-04-27）
3. `/knowledge/mindmap` — ForceGraph/MindMapTree 視圖切換無 Feature Scenario（首見：2026-04-24）
4. `/exam/results` — 成績卡片下載按鈕無 Feature Scenario（首見：2026-04-24）
5. **【2026-04-29 新增】** `/exam/workspace` — Feature 05 要求「AI 教練打氣介面（Certi）」在測驗開始時顯示，頁面無任何對應 UI 實作
6. `/super-admin/settings/version` — 版本資訊頁無 Feature 覆蓋（首見：2026-04-24）
7. `/super-admin/platform-subjects` — 平台科目管理無 Feature 覆蓋（首見：2026-04-27）
8. `/resources/[id]/candidates` — 候選考題管理無 Feature 覆蓋（首見：2026-04-27）

### 🟠 實作缺失（Feature 存在但頁面缺功能）

1. `/exam/results` — Feature 06 描述「逐題解析」，頁面無跳轉入口按鈕（首見：2026-04-24）
2. `/exam/results` — 成績卡片下載為 `alert("即將推出")` stub（首見：2026-04-24）
3. `/super-admin/anomaly` — Feature 16「批次修復」情境缺對應 UI（首見：2026-04-24）
4. **【2026-04-29 新增】** `/review` — UI 顯示 KaTeX disclaimer 但 `katex`/`react-katex` 未直接 import；MathContent 是否實際執行 KaTeX 渲染待確認；Feature 07 無對應 Scenario
5. `/knowledge` — 「+ 新增資源」按鈕導向 `/dashboard` 而非直接開 modal，Feature 03 無 Scenario 覆蓋（首見：2026-04-28）

### 🟡 空態需補強（需查 Job 表）

1. `/review` — `wrongQuestions.length === 0` 顯示「全部答對！」但未查 `exam_generation_jobs`（首見：2026-04-28）
2. `/practice` — no-questions 空態有提示文字但未實際查詢 `resource_parse_jobs.failure_reason`（首見：2026-04-24）
3. **【2026-04-29 新增】** `/schedule` — `recs.length === 0` 直接顯示「尚無備考科目」，未查詢 schedule 相關 job 表，無法區分「真正無科目」vs「job 失敗」
4. **【2026-04-29 新增】** `/verify-email/sent` — resend 重寄失敗時 `catch {}` block 為空（silent fail），使用者無任何錯誤提示，違反 Feature 01 UX 規範

### ✅ 本次確認已解決（今日 2026-04-29 驗證）

1. `/exam/setup` — Feature 19 排列模式（interleaved/grouped/sequential）已實作為 3 按鈕 UI（`orderMode` state 及 JSX 確認存在）
2. `/exam/workspace` — PomodoroTimer 在 line 226 確認渲染（`<PomodoroTimer examDurationSec={totalTimeLimit} paused={isPaused} />`），Feature 21 覆蓋完整
3. `/library` — ToDoList 中的 `/library` 條目為**過時參照**（前端路由無此 page.tsx），建議清除

---

*本 checklist 由自動 QA 巡檢工具產出，依據 CLAUDE.md QA 三層驗收原則執行*
