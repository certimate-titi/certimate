# CertiMate Daily QA Issue Checklist
**產出時間**：2026-04-27 01:09 (Asia/Taipei)
**審查頁面數**：48 頁
**Feature File 數**：46 個
**發現問題總計**：🔴 22 + 🟠 5 + 🟡 2

---

## 頁面審查清單

### /login — 身分驗證

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email 輸入欄 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 密碼輸入欄 + 顯示切換 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | showPassword toggle |
| Google 登入按鈕 | 按鈕 | ✅ 01-身分驗證.feature | ✅ 實作 | useGoogleLogin hook |
| Remember Me 勾選 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | localStorage/sessionStorage |
| 登入失敗錯誤訊息 | 空/錯誤態 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 忘記密碼連結 | 連結 | ✅ 01-身分驗證.feature | ✅ 實作 | → /forgot-password |
| 前往註冊連結 | 連結 | ✅ 01-身分驗證.feature | ✅ 實作 | → /signup |

**問題**：無

---

### /signup — 註冊

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email/密碼表單 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| Google SSO 登入（GoogleLogin） | 按鈕 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 服務條款/隱私權同意勾選 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 條款 Modal 彈窗（LegalModal） | 互動 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 密碼強度指示條 | 顯示 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 重複密碼確認 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |

**問題**：無

---

### /forgot-password — 忘記密碼

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email 輸入欄 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 送出重設信按鈕 | 按鈕 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| SSO 用戶提示訊息 | 顯示 | ✅ 01-身分驗證.feature | ✅ 實作 | |

**問題**：無

---

### /reset-password — 重設密碼

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 新密碼輸入欄 + 強度指示 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |
| 確認密碼欄 | 表單 | ✅ 01-身分驗證.feature | ✅ 實作 | |

**問題**：無

---

### /onboarding — 首次引導

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 進度列（4 步驟） | 顯示 | ✅ 15-首次登入引導.feature | ✅ 實作 | |
| Step 1 歡迎 + 個人資訊表單 | 顯示/表單 | ✅ 15-首次登入引導.feature | ✅ 實作 | |
| Step 2 科目選擇器（至少選一科驗證） | 互動 | ✅ 15-首次登入引導.feature | ✅ 實作 | |
| Step 3 偏好設定 | 表單 | ✅ 15-首次登入引導.feature | ✅ 實作 | |
| Step 4 確認畫面 | 顯示 | ✅ 15-首次登入引導.feature | ✅ 實作 | |
| 上一步/下一步按鈕 | 按鈕 | ✅ 15-首次登入引導.feature | ✅ 實作 | |

**問題**：無

---

### /dashboard — 個人儀表板（核心頁）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 問候語 + 姓名顯示 | 顯示 | ✅ 13-個人儀表板.feature（全 @ignore） | ⚠️ @ignore | |
| 備考模式標籤（Sprint/Standard/Mastery） | 顯示/互動 | 🔴 無任何 Feature 覆蓋 | ✅ 實作 | |
| 科目切換器（SubjectSwitcher） | 互動 | 🔴 13 全 @ignore，無 active | ✅ 實作 | |
| ＋ 新增科目（SubjectPickerModal） | 互動 | 🔴 無 active Scenario | ✅ 實作 | |
| StreakCounter（連續學習天數） | 顯示 | 🔴 無 active Scenario | ✅ 實作 | |
| 核心指標卡（距考試/答題數/答對率/預測及格率） | 顯示 | 🔴 無 active Scenario | ✅ 實作 | |
| 資源上傳區（檔案/YouTube） | 互動 | ✅ 02-資源上傳.feature | ✅ 實作 | |
| 上傳狀態回饋（pending/processing/completed/failed） | 顯示 | ✅ 02-資源上傳.feature | ✅ 實作 | |
| 每日任務（DailyQuestCard） | 顯示 | 🔴 13 全 @ignore | ✅ 實作 | |
| 待辦提醒（activityItems） | 顯示 | 🔴 無 active Scenario | ✅ 實作 | |
| 複習日曆 + 月份切換 | 顯示/互動 | 🔴 無 active Scenario | ✅ 實作 | |
| 今日特訓 + 開始特訓/複習按鈕 | 互動 | ✅ 07-錯題複習.feature | ✅ 實作 | |
| 學習狀態 + DomainRadarChart | 顯示 | 🔴 13 全 @ignore | ✅ 實作 | |
| StudyBuddyBanner（ULTRA） | 顯示 | 🔴 無任何 Feature 覆蓋 | ✅ 實作 | |
| AnnouncementBanner | 顯示 | ✅ 24-系統公告管理.feature | ✅ 實作 | |
| 意見反饋連結 | 連結 | ✅ 17-意見反饋.feature | ✅ 實作 | |
| 無科目空態引導 | 空態 | ✅ 13-個人儀表板.feature | ✅ 實作 | |

**問題**：
- 🔴 備考模式標籤 / StudyBuddyBanner 無任何 Feature 覆蓋
- 🔴 科目切換器、StreakCounter、核心指標卡、每日任務、待辦提醒、複習日曆、DomainRadarChart — Feature 13 全 @ignore，無 active Scenario

---

### /knowledge — 知識庫（核心頁）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目切換器 | 互動 | ✅ 03-知識心智圖.feature | ✅ 實作 | |
| 文件列表（PDF/YouTube/圖片） | 顯示 | ✅ 11-資源庫管理.feature | ✅ 實作 | |
| 節點選擇 → 節點詳情面板（NodeDetailPanel） | 互動 | ✅ 03-知識心智圖.feature | ✅ 實作 | |
| MindMapTree 心智圖樹 | 顯示 | ✅ 03b-知識心智圖導航.feature | ✅ 實作 | |
| ForceGraph 力導向圖（Canvas） | 顯示 | ✅ 46-知識地圖Canvas.feature | 🟠 三層 Zoom 未確認 | |
| AI 教練對話框（ScaffoldNotebook） | 互動 | ✅ 03-知識心智圖.feature | ✅ 實作 | 付費牆 |
| 搜尋 / 刪除資源 | 互動 | ✅ 11-資源庫管理.feature | ✅ 實作 | |
| 節點練習按鈕（→ /practice） | 互動 | ✅ 32-節點練習模式.feature | ✅ 實作 | |
| 出題按鈕（→ /exam/setup） | 互動 | ✅ 04-測驗設定.feature | ✅ 實作 | |
| FAILED 資源 failure_reason 顯示 | 空態 | ✅ 02-資源上傳.feature | ✅ 實作 | 查 job 表 |

**問題**：
- 🟠 Feature 46（Canvas 三層 Zoom）的 Tier1/2/3 API（`/canvas` + `/canvas/children/{id}`）在頁面中未見明確呼叫，需確認三層下鑽是否完整實作

---

### /knowledge/mindmap — 全螢幕心智圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目切換器 | 互動 | ✅ 03-知識心智圖.feature | ✅ 實作 | |
| MindMapTree 樹狀圖 | 顯示 | ✅ 03b-知識心智圖導航.feature | ✅ 實作 | |
| ForceGraph 力導向圖 | 顯示 | ✅ 46-知識地圖Canvas.feature | ✅ 實作 | |
| 視圖切換按鈕（tree/force） | 互動 | 🔴 無任何 Feature Scenario | ✅ 實作 | |
| 節點點擊互動 | 互動 | ✅ 03b-知識心智圖導航.feature | ✅ 實作 | |
| 空態處理（4 種情境） | 空態 | ✅ 實作 | ✅ 實作 | |

**問題**：
- 🔴 視圖切換（tree/force toggle）無任何 Feature Scenario

---

### /exam/setup — 測驗設定（核心頁）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目切換器 | 互動 | ✅ 04-測驗設定.feature | ✅ 實作 | |
| 資源文件選擇 + 系統節點選擇 | 顯示/互動 | ✅ 04-測驗設定.feature | ✅ 實作 | |
| 題數 / 難度 / 模式 / 題型設定 | 互動 | ✅ 04-測驗設定.feature | ✅ 實作 | |
| 方案限制 Lock 提示 | 顯示 | ✅ 04-測驗設定.feature | ✅ 實作 | |
| 進階 Bloom 比例配方（管理員） | 互動 | ✅ 18-題目分類.feature | ✅ 實作 | |
| 生成考卷按鈕（AI loading overlay） | 按鈕 | ✅ 04a-AI考題生成.feature | ✅ 實作 | |
| 無資源空態提示（引導查知識庫） | 空態 | ✅ 02-資源上傳.feature | ✅ 實作 | |

**問題**：無

---

### /exam/workspace — 模擬機考（核心頁）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 倒數計時 + 暫停/恢復 | 顯示/互動 | ✅ 05-模擬機考.feature | ✅ 實作 | |
| 題目顯示 + 選項 A/B/C/D | 顯示 | ✅ 05-模擬機考.feature | ✅ 實作 | |
| 上一題/下一題 + 標記複查 | 互動 | ✅ 05-模擬機考.feature | ✅ 實作 | |
| 題目總覽 Grid | 互動 | ✅ 05-模擬機考.feature | ✅ 實作 | |
| 提交確認 Modal（未答題提示） | 互動 | ✅ 05-模擬機考.feature | ✅ 實作 | |
| LocalStorage 自動儲存 | 邏輯 | ✅ 05-模擬機考.feature | ✅ 實作 | |
| 時間耗盡自動提交 | 邏輯 | ✅ 05-模擬機考.feature | ✅ 實作 | |
| 番茄鐘（Pomodoro） | 互動 | ✅ 21-番茄鐘.feature（15 active） | 🟠 頁面無實作 | Feature 21 完整 active |

**問題**：
- 🟠 Feature 21（番茄鐘）有 15 個 active Scenario，但 `/exam/workspace` 頁面無 Pomodoro 相關 UI 或邏輯，需實作

---

### /exam/results — 測驗結果（核心頁）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 總分 + 合格/未合格 + 分數比較 | 顯示 | ✅ 06-測驗結果.feature | ✅ 實作 | |
| 答對/答錯/未答 統計 | 顯示 | ✅ 06-測驗結果.feature | ✅ 實作 | |
| AI 教練介入橫幅（連續退步） | 顯示 | ✅ 06-測驗結果.feature | ✅ 實作 | |
| 完賽數據（時間/均速/標記答對率） | 顯示 | ✅ 06-測驗結果.feature | ✅ 實作 | |
| 逐題解析入口按鈕 | 按鈕 | ✅ 06-測驗結果.feature | 🟠 缺少明確入口 | Feature 有 Scenario |
| 成績卡片下載（Download） | 按鈕 | 🔴 無 Feature Scenario | 🟠 為 alert stub | |
| 複習錯題按鈕（→ /review） | 按鈕 | ✅ 07-錯題複習.feature | ✅ 實作 | |
| 領域分析 + ForceGraph 知識圖譜 | 顯示 | ✅ 06/46 feature | ✅ 實作 | |
| AI 摘要（aiSummary） | 顯示 | ✅ 06-測驗結果.feature | ✅ 實作 | |
| Confetti 高分動畫（≥80分） | 顯示 | ✅ 06-測驗結果.feature | ✅ 實作 | |

**問題**：
- 🟠 逐題解析查看（Feature 06 有 Scenario），頁面 `questions` 有資料但無跳轉逐題解析的明確按鈕
- 🔴 成績卡片下載（Download icon）無 Feature Scenario，且為 alert stub

---

### /practice — 節點練習（核心頁）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目切換器 | 互動 | ✅ 32-節點練習模式.feature | ✅ 實作 | |
| 知識節點樹列表（葉節點） | 顯示 | ✅ 32-節點練習模式.feature | ✅ 實作 | |
| 節點選擇 → 載入題目 | 互動 | ✅ 32-節點練習模式.feature | ✅ 實作 | |
| 選項作答 + 提交 + 解析回饋 | 互動 | ✅ 32-節點練習模式.feature | ✅ 實作 | |
| 下一題 + 答對率統計 | 互動/顯示 | ✅ 32-節點練習模式.feature | ✅ 實作 | |
| blindInferenceService（信心度校準） | 邏輯 | ✅ 20-信心度校準.feature | ✅ 實作 | |
| 無題目空態（no-questions） | 空態 | ✅ 32-節點練習模式.feature | 🟡 未查 job 表 | 僅文字引導 |
| 「前往出題」+「選擇其他節點」+「回知識圖譜」 | 按鈕 | ✅ 32-節點練習模式.feature | ✅ 實作 | |

**問題**：
- 🟡 no-questions 空態有文字 hint，但**未實際呼叫 resource_parse_jobs API 查詢 failure_reason**，僅文字引導用戶

---

### /review — 錯題複習（核心頁）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目切換器 | 互動 | ✅ 07-錯題複習.feature | ✅ 實作 | |
| 錯題列表（左側 Sidebar） | 顯示 | ✅ 07-錯題複習.feature | ✅ 實作 | |
| 題目詳情（正確/使用者答案比對） | 顯示 | ✅ 07-錯題複習.feature | ✅ 實作 | |
| 解析（FREE 鎖定毛玻璃 / PRO+ 解鎖） | 顯示 | ✅ 07-錯題複習.feature | ✅ 實作 | |
| AI 教練對話框（僅 PRO+） | 互動 | ✅ 07-錯題複習.feature | ✅ 實作 | |
| 引用來源切換（showCitation） | 互動 | ✅ 07-錯題複習.feature | ✅ 實作 | |
| 全部答對空態 | 空態 | ✅ 07-錯題複習.feature | ✅ 實作 | |

**問題**：無

---

### /library — 資源庫（含知識地圖 Tab）

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Tab 切換（我的素材/知識地圖） | 互動 | 🔴 無 Feature 覆蓋 | ✅ 實作 | hash routing |
| 素材 Tab → ResourceLibraryPage | 顯示 | ✅ 11-資源庫管理.feature | ✅ 實作（嵌入） | |
| 知識地圖 Tab → KnowledgeBasePage | 顯示 | ✅ 03-知識心智圖.feature | ✅ 實作（嵌入） | |
| Tab 切換後空態 | 空態 | 🟡 未確認 | 🟡 需確認 | |

**問題**：
- 🔴 Tab 切換（我的素材/知識地圖）無任何 Feature Scenario
- 🟡 Tab 切換後空態是否查詢 job 狀態不明

---

### /account — 帳號設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 個人資料 Tab（姓名/年齡/學歷/職業）+ 儲存 | 表單 | ✅ 22-帳號設定.feature | ✅ 實作 | |
| 帳單/訂閱 Tab | 顯示 | ✅ 08-訂閱管理.feature | ✅ 實作 | |
| 安全 Tab（密碼變更） | 表單 | ✅ 22-帳號設定.feature | ✅ 實作 | |
| 偏好設定 Tab（通知/暗色模式） | 互動 | ✅ 22-帳號設定.feature | ✅ 實作（localStorage） | |
| 成就 Tab（AchievementGrid） | 顯示 | ✅ 13-個人儀表板.feature（@ignore） | ⚠️ @ignore | |
| 帳號刪除 Modal | 互動 | ✅ 22-帳號設定.feature | ✅ 實作 | |

**問題**：無

---

### /account/my-subjects — 我的自建考科

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 自建科目列表（名稱/描述/建立日期） | 顯示 | 🔴 無 Feature 覆蓋 | ✅ 實作 | |
| 刪除科目按鈕（確認彈窗） | 互動 | 🔴 無 Feature 覆蓋 | ✅ 實作 | |
| 無科目空態 | 空態 | 🔴 無 Feature 覆蓋 | ✅ 實作 | |

**問題**：
- 🔴 自建科目管理（列表/刪除）無任何 Feature Scenario 覆蓋

---

### /account/resource-library — 資源庫管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 資源列表（badge: 官方/EDU/個人） | 顯示 | ✅ 11-資源庫管理.feature | ✅ 實作 | |
| 搜尋關鍵字 | 互動 | ✅ 11-資源庫管理.feature | ✅ 實作 | |
| 解析狀態 badge + FAILED failure_reason（tooltip） | 顯示 | ✅ 02-資源上傳.feature | ✅ 實作 | 查 job 表 |
| 刪除資源（確認彈窗） | 互動 | ✅ 11-資源庫管理.feature | ✅ 實作 | |
| ULTRA 分享/撤回（Share） | 互動 | ✅ 11-資源庫管理.feature | ✅ 實作 | |
| 解析進度輪詢（3s） | 邏輯 | ✅ 02-資源上傳.feature | ✅ 實作 | |

**問題**：無

---

### /pricing — 定價頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 4 個方案卡（FREE/PRO/PRO+/ULTRA） | 顯示 | ✅ 18-定價與升級引導.feature（@ignore） | ✅ 實作 | |
| 功能比較 + 當前方案標記 + 升級 CTA | 顯示 | ✅ 18-定價與升級引導.feature | ✅ 實作 | |
| EDU 方案說明區塊 | 顯示 | ✅ 18-定價與升級引導.feature | ✅ 實作 | |

**問題**：無（Feature 18 @ignore 已有記錄）

---

### /feedback — 意見反饋

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 反饋類型選擇（BUG/FEATURE/CONTENT/OTHER） | 互動 | ✅ 17-意見反饋.feature | ✅ 實作 | |
| 主旨/內容輸入 + 截圖上傳（≤3張） | 表單 | ✅ 17-意見反饋.feature | ✅ 實作 | |
| 提交按鈕 + 提交成功狀態 | 按鈕 | ✅ 17-意見反饋.feature | ✅ 實作 | |
| 我的反饋歷史（可展開/收合） | 顯示 | ✅ 17-意見反饋.feature | ✅ 實作 | |

**問題**：無

---

### /edu-console — EDU 機構後台

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 學員列表（Student 卡片） | 顯示 | 🔴 Feature 10 全 @ignore | ✅ 實作 | |
| 搜尋學員 | 互動 | 🔴 無 active Scenario | ✅ 實作 | |
| CSV 匯入 Modal（ImportStudentModal） | 互動 | 🔴 Feature 10 全 @ignore | ✅ 實作 | |
| 下載 CSV 範本 | 按鈕 | 🔴 無 active Scenario | ✅ 實作 | |
| 學員 CompetencyBar 進度 | 顯示 | 🔴 無 active Scenario | ✅ 實作 | |
| 發送 AI 摘要報告 | 按鈕 | 🔴 無 active Scenario | ✅ 實作 | |

**問題**：
- 🔴 Feature 10（B2B 機構管理後台）全 @ignore，所有功能無 active Scenario

---

### /resources/[id]/candidates — 候選考題管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 候選考題列表/管理 | 顯示/互動 | 🔴 無任何 Feature 覆蓋 | ✅ 實作 | |

**問題**：
- 🔴 無任何 Feature 覆蓋（Feature 23/25 未對應此路徑）

---

### /super-admin/* — 管理後台各頁

| 頁面 | 主要元素 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|---------|-------------|---------|------|
| /super-admin/dashboard | KPI 卡片/趨勢圖 | ✅ 12-平台管理後台（@ignore） | ✅ 實作 | |
| /super-admin/users | 用戶列表/搜尋/分頁 | ✅ 12（@ignore） | ✅ 實作 | |
| /super-admin/users/[userId] | 用戶詳情/停權/通知 | 🔴 無 active Scenario | ✅ 實作 | Feature 12 @ignore |
| /super-admin/moderation | 審核佇列/反饋管理 | ✅ 12b（active） | ✅ 實作 | |
| /super-admin/finance | 財務報表 | ✅ 12a（active） | ✅ 實作 | |
| /super-admin/anomaly | 異常列表/維修任務 | ✅ 16（active） | ✅ 實作 | 批次修復缺 Scenario |
| /super-admin/cost-monitor | 成本卡片/趨勢圖 | ✅ 33（@ignore） | ✅ 實作 | |
| /super-admin/exam-import | 匯入表單/監控 | ✅ 32-考古題匯入（active） | ✅ 實作 | |
| /super-admin/audit-logs | 審計日誌 | 🔴 Feature 12 全 @ignore | ✅ 實作 | |
| /super-admin/retirement | 考題退場確認 | 🔴 Feature 25 全 @ignore | ✅ 實作 | |
| /super-admin/default-resources | 預設資源 Fork | 🔴 Feature 34 無頁面 Scenario | ✅ 實作 | |
| /super-admin/platform-subjects | 平台科目管理 | 🔴 無任何 Feature 覆蓋 | ✅ 實作 | |
| /super-admin/prompt-templates | Prompt 模板列表 | ✅ 30（active） | ✅ 實作 | |
| /super-admin/prompt-templates/new | 新增模板 | ✅ 30（active） | ✅ 實作 | |
| /super-admin/prompt-templates/[id] | 模板詳情/編輯/A/B | ✅ 30（active） | ✅ 實作 | |
| /super-admin/settings | AI 模型路由 | ✅ 12c（active） | ✅ 實作 | |
| /super-admin/settings/admins | 管理員 CRUD | ✅ 12c（active） | ✅ 實作 | |
| /super-admin/settings/announcements | 公告管理 | ✅ 24（active） | ✅ 實作 | |
| /super-admin/settings/flags | Feature Flag | 🔴 無 active Scenario | ✅ 實作 | |
| /super-admin/settings/plans | 方案配額管理 | 🔴 無 active Scenario | ✅ 實作 | |
| /super-admin/settings/version | 版本資訊 | 🔴 無任何 Feature 覆蓋 | ✅ 實作 | |

---

## Feature File 覆蓋摘要

| Feature File | Scenario 數 | @ignore 狀態 | 備註 |
|-------------|------------|------------|------|
| 01-身分驗證.feature | 25+ | 無 | 完整覆蓋 |
| 02-資源上傳.feature | 20+ | 無 | 完整覆蓋 |
| 03-知識心智圖.feature | 10 | 無 | 完整覆蓋 |
| 03a-知識心智圖生成.feature | 8 | 無 | 完整覆蓋 |
| 03b-知識心智圖導航.feature | 6 | 無 | 完整覆蓋 |
| 04-測驗設定.feature | 15+ | 無 | 完整覆蓋 |
| 04a-AI考題生成服務.feature | 8 | 無 | 完整覆蓋 |
| 05-模擬機考.feature | 12+ | 無 | 完整覆蓋 |
| 06-測驗結果.feature | 10+ | 無 | 完整覆蓋 |
| 07-錯題複習與AI教練.feature | 13+ | 6（@playwright-e2e） | 主要 active |
| 08-訂閱管理.feature | 10+ | Feature-level @ignore | 全 @ignore |
| 08a-綠界金流串接.feature | 8 | 無 | 完整覆蓋 |
| 08b-付款後權限更新.feature | 5 | 無 | 完整覆蓋 |
| 09-學習記憶排程.feature | 8 | 無 | 完整覆蓋 |
| 10-B2B機構管理後台.feature | 15+ | Feature-level @ignore | 全 @ignore |
| 11-資源庫管理.feature | 15+ | 無 | 完整覆蓋 |
| 12-平台管理後台.feature | 10+ | Feature-level @ignore | 全 @ignore |
| 12a-平台管理後台-財務管理.feature | 8 | 無 | 完整覆蓋 |
| 12b-平台管理後台-內容審核.feature | 8 | 無 | 完整覆蓋 |
| 12c-平台管理後台-系統設定.feature | 6 | 無 | 完整覆蓋 |
| 13-個人儀表板與成就系統.feature | 35+ | Feature-level @ignore | 全 @ignore |
| 14-社群歸屬與主動關懷.feature | 8 | 無 | 完整覆蓋 |
| 15-首次登入引導與學習歷程建立.feature | 12+ | 無 | 完整覆蓋 |
| 16-異常維修管理.feature | 8 | 無 | 完整覆蓋 |
| 17-意見反饋.feature | 10+ | 無 | 完整覆蓋 |
| 18-定價與升級引導.feature | 8 | Feature-level @ignore | 全 @ignore |
| 18-題目分類與考試趨勢分析.feature | 6 | 無 | 完整覆蓋 |
| 19-交錯練習.feature | 8 | 無 | 完整覆蓋 |
| 20-信心度校準.feature | 6 | 2（UI level） | 主要 active |
| 21-番茄鐘學習節奏.feature | 15 | 無 | 完整 active，但頁面未實作 |
| 22-帳號設定與個人偏好.feature | 10+ | 無 | 完整覆蓋 |
| 23-考古題題庫管理.feature | 8 | 無 | 完整覆蓋 |
| 24-系統公告管理.feature | 8 | 無 | 完整覆蓋 |
| 25-AI考題退場與放榜確認.feature | 8 | Feature-level @ignore | 全 @ignore |
| 26-考綱逆向工程.feature | 6 | 無 | 完整覆蓋 |
| 27-個人化錯題地圖.feature | 8 | Feature-level @ignore | 全 @ignore |
| 28-階層式難度遞進.feature | 6 | 無 | 完整覆蓋 |
| 29-知識樹合併對齊.feature | 6 | 無 | 完整覆蓋 |
| 30-Prompt模板管理.feature | 20+ | 無 | 完整覆蓋 |
| 31-多租戶安全與資料隔離.feature | 8 | 無 | 完整覆蓋 |
| 32-節點練習模式.feature | 9 | 無 | 完整覆蓋 |
| 32-考古題現代化匯入.feature | 8 | 無 | 完整覆蓋 |
| 33-成本監控中心.feature | 10+ | Feature-level @ignore | 全 @ignore |
| 34-預載科目Fork.feature | 6 | 無 | 無對應前端頁面 Scenario |
| 46-知識地圖Canvas.feature | 6 | 無 | 完整覆蓋 |
| 46b-Analytics事件接收.feature | 4 | 無 | 完整覆蓋 |

---

## 問題彙整

### 🔴 Feature 缺失（共 22 項）

1. `/dashboard` — 備考模式標籤（Sprint/Standard/Mastery tooltip）無任何 Feature 覆蓋
2. `/dashboard` — StudyBuddyBanner（ULTRA 共讀）無任何 Feature 覆蓋
3. `/dashboard` — 科目切換器（SubjectSwitcher + 新增科目）無 active Scenario（Feature 13 全 @ignore）
4. `/dashboard` — StreakCounter（連續學習天數）無 active Scenario
5. `/dashboard` — 核心指標卡（距考試天數/累積答題數/答對率/預測及格率）無 active Scenario
6. `/dashboard` — 每日任務（DailyQuestCard）無 active Scenario
7. `/dashboard` — 待辦提醒（activityItems）無 active Scenario
8. `/dashboard` — 複習日曆 + 月份切換按鈕無 active Scenario
9. `/dashboard` — DomainRadarChart（領域雷達圖）無 active Scenario
10. `/knowledge/mindmap` — 視圖切換按鈕（tree/force toggle）無任何 Feature Scenario
11. `/exam/results` — 成績卡片下載（Download 按鈕）無 Feature Scenario
12. `/account/my-subjects` — 自建科目列表 + 刪除功能無任何 Feature 覆蓋
13. `/library` — Tab 切換（我的素材/知識地圖）無任何 Feature Scenario
14. `/edu-console` — Feature 10 全 @ignore，CSV 匯入/學員管理/批次操作無 active Scenario
15. `/super-admin/users/[userId]` — 無 active Feature Scenario（Feature 12 全 @ignore）
16. `/super-admin/settings/flags` — Feature Flag 管理無任何 active Scenario
17. `/super-admin/settings/plans` — 方案配額管理無 active Scenario
18. `/super-admin/settings/version` — 版本資訊頁無任何 Feature 覆蓋
19. `/super-admin/audit-logs` — 審計日誌無 active Feature Scenario（Feature 12 全 @ignore）
20. `/resources/[id]/candidates` — 候選考題管理頁面無任何 Feature 覆蓋
21. `/super-admin/retirement` — Feature 25 全 @ignore，考題退場無 active Scenario
22. `/super-admin/platform-subjects` — 平台科目管理無任何 Feature 覆蓋

### 🟠 實作缺失（共 5 項）

1. `/exam/results` — Feature 06 描述「逐題解析查看」，頁面有 `questions` 資料但無跳轉逐題解析的明確按鈕入口
2. `/exam/results` — 成績卡片下載（Download icon）為 alert stub，需實作實際下載功能
3. `/exam/workspace` — Feature 21（番茄鐘學習節奏）有 15 個 active Scenario，但頁面無 Pomodoro 相關 UI 或邏輯
4. `/knowledge` — Feature 46（Canvas 三層 Zoom）的 Tier 1/2/3 分層 API（`/canvas` + `/canvas/children/{id}`）在頁面中未見明確呼叫
5. `/super-admin/anomaly` — Feature 16 無「批次修復」Scenario，頁面相關批次修復功能缺失

### 🟡 空態需補強（共 2 項）

1. `/practice` — no-questions 空態有文字 hint，但**未實際呼叫 resource_parse_jobs API 取得 failure_reason**，需補強至主動查 job 表
2. `/library` — Tab 切換後空態情況不明，建議確認是否查詢相關 job 狀態（resource_parse_jobs 等）
