# CertiMate Daily QA Issue Checklist
**產出時間**：2026-05-07 01:14 (Asia/Taipei)
**審查頁面數**：50 頁
**Feature File 數**：44 個
**發現問題總計**：🔴 2 + 🟠 1 + 🟡 1（今日新增；既有追蹤問題詳見 ToDoList.md）

---

## 頁面審查清單（核心頁面優先）

### /dashboard — 主控台首頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 歡迎標題 + 使用者名稱 | 顯示 | ✅ 13-個人儀表板 | ✅ 實作 | |
| 學習模式標籤（Sprint/Standard/Mastery/Final）+ Tooltip | 按鈕 | 🔴 無 Feature Scenario | ✅ 實作 | 首見 2026-05-06，已追蹤於 ToDoList |
| StreakCounter 連勝火焰 | 顯示 | ✅ 13 Rule「連勝天數」 | ✅ 實作 | |
| 考試倒數天數卡片 | 顯示 | ✅ 13 Rule「考試倒數」 | ✅ 實作 | |
| 累積答題數卡片 | 顯示 | ✅ 13 | ✅ 實作 | |
| 整體答對率卡片 | 顯示 | ✅ 13 | ✅ 實作 | |
| 預測及格率卡片 | 顯示 | ✅ 13 | ✅ 實作 | |
| 快速匯入資源（上傳檔案 + YouTube） | 按鈕 | ✅ 02-資源上傳 | ✅ 實作 | |
| QuotaBadge（月上傳配額顯示） | 顯示 | ✅ 08 | ✅ 實作 | |
| 每日任務列表（DailyQuestCard） | 顯示 | ✅ 13 Rule「每日微任務」 | ✅ 實作 | |
| 待辦提醒（activityItems） | 顯示 | ✅ 13 | ✅ 實作 | |
| ScheduleWeekCard（學習排程） | 顯示 | ✅ 09 | ✅ 實作 | |
| DomainRadarChart（雷達圖）| 顯示 | ✅ 13 | ✅ 實作 | |
| AnnouncementBanner（公告橫幅） | 顯示 | ✅ 24 | ✅ 實作 | |
| PendingJourneysBanner（待確認旅程） | 顯示 | ✅ 25 | ✅ 實作 | |
| 科目切換器（SubjectSwitcher） | 按鈕 | 🔴 Feature 13 仍有 active Scenario | ⚠️ 已移除（2026-05）| **今日新問題**：Feature 未同步更新 |
| 無科目時「開始選擇科目」modal | 按鈕 | 🔴 Feature 15 未覆蓋 | ✅ 實作 | 首見 2026-05-06，已追蹤 |
| 意見反饋連結 | 連結 | ✅ 17 | ✅ 實作 | |

**今日新問題**：
- 🔴 Feature 13（L40-58）仍有 active Scenarios 要求 dashboard 顯示科目切換器（「備考多科時顯示科目切換器應包含 AWS SAA、TOEIC」、「切換科目後儀表板數據更新」），但 SubjectSwitcher 已於 2026-05 移除，Feature 13 Scenarios 未同步更新。

---

### /knowledge — 知識地圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher（科目切換） | 按鈕 | ✅ 03、11 | ✅ 實作 | |
| 文件列表（左側面板） | 顯示 | ✅ 11 | ✅ 實作 | |
| 搜尋框（文件過濾） | 輸入 | ✅ 03 Rule「搜尋知識點篩選」 | ⚠️ 只過濾文件列表 | **今日新問題** |
| ForceGraph（圖譜視圖） | 互動 | ✅ 03b | ✅ 實作 | |
| MindMapTree（列表視圖） | 互動 | ✅ 03b | ✅ 實作 | |
| 文件視圖切換 | 按鈕 | ✅ 03b | ✅ 實作 | |
| NodeDetailPanel（節點詳情） | 顯示 | ✅ 03、03b | ✅ 實作 | |
| AI 教練對話框 | 互動 | ✅ 03b Rule「付費牆」 | ✅ 實作 | |
| 升級提示（PRO 配額用盡鎖屏） | 顯示 | ✅ 03b | ✅ 實作 | |
| 節點練習按鈕 | 按鈕 | ✅ 32 | ✅ 實作 | |
| 節點測驗按鈕 | 按鈕 | ✅ 04 | ✅ 實作 | |
| 資源刪除按鈕（HardDeleteConfirmModal） | 按鈕 | ✅ 36 | ✅ 實作 | |
| 解析失敗 badge + failure_reason（Layer 3） | 顯示 | ✅ 11 | ✅ 實作 | |
| 全部重新解析按鈕（空圖譜/全失敗時） | 按鈕 | ✅ 11 | ✅ 實作 | |
| 知識樹萃取按鈕 | 按鈕 | ✅ 03a | ✅ 實作 | |
| 「錯題地圖」連結按鈕 | 連結 | ✅ 27 | ✅ 實作 | |
| 空態多情境區分（Layer 3）| 顯示 | ✅ 03b | ✅ 實作 | 4 種情境已完整 |

**今日新問題**：
- 🟠 Feature 03 Rule「搜尋知識點可即時篩選心智圖導覽區的節點」Scenario 描述「右側心智圖導覽區應僅顯示包含 'S3' 關鍵字的知識節點」。但 knowledge/page.tsx 的 `searchQuery` 只用於過濾左側文件列表（L614），未傳入 MindMapTree 或 ForceGraph 元件進行節點過濾。

---

### /knowledge/wrong-answers — 錯題熱力圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 錯題節點熱力圖（紅/橘/綠/灰） | 顯示 | ✅ 27 | ✅ 實作 | |
| 節點展開錯題明細 | 互動 | ✅ 27 | ✅ 實作 | |
| 空態 Layer 3（查 parse jobs） | 顯示 | ✅ CLAUDE.md Layer 3 | ✅ 實作 | |
| 返回知識庫按鈕 | 連結 | ✅ | ✅ 實作 | |

---

### /knowledge/mindmap — 心智圖

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| ForceGraph / MindMapTree 切換 | 按鈕 | ✅ 03b | ✅ 實作 | |
| 節點點擊詳情側邊面板 | 互動 | ✅ 03b | ✅ 實作 | |
| 「開始練習此節點」按鈕 | 連結 | ✅ 32 | ✅ 實作 | |
| 空態 Layer 3（查 parse jobs） | 顯示 | ✅ CLAUDE.md | ✅ 實作 | |

---

### /exam/setup — 測驗設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| SubjectSwitcher | 按鈕 | ✅ 04 | ✅ 實作 | |
| 文件選擇（範圍勾選） | 互動 | ✅ 04 | ✅ 實作 | |
| 系統知識節點選擇 | 互動 | ✅ 04 | ✅ 實作 | |
| 出題模式（AI混合/純考古/錯題） | 按鈕 | ✅ 04 | ✅ 實作 | |
| 題目排列模式（交錯/分組/依難度） | 按鈕 | ✅ 19 | ✅ 實作 | |
| 題數選擇（10/20/50/100，tier 限制） | 按鈕 | ✅ 04 | ✅ 實作 | |
| 難度選擇（1/2/3） | 按鈕 | ✅ 04 | ✅ 實作 | |
| 進階配方（ULTRA+SUPER_ADMIN，Bloom 比例） | 互動 | ✅ 04 | ✅ 實作 | |
| QuotaBadge（月測驗配額） | 顯示 | ✅ 08 | ✅ 實作 | |
| 真實進度條動畫（輪詢後端） | 顯示 | ✅ 04 | ✅ 實作 | |
| 空文件態提示（靜態文字） | 顯示 | 🟡 未查 job 表 | ⚠️ 提示存在但不夠深入 | **今日新問題** |

---

### /exam/workspace — 模擬機考

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 題目顯示 + 選項 | 顯示 | ✅ 05 | ✅ 實作 | |
| 答案選擇 | 互動 | ✅ 05 | ✅ 實作 | |
| 信心度校準（😰😐😎） | 按鈕 | ✅ 20 | ✅ 實作 | |
| PomodoroTimer（番茄鐘倒數顯示） | 顯示 | ✅ 21 | ✅ 實作 | |
| 番茄鐘啟用開關 + 設定 UI | 按鈕 | 🔴 Feature 21 | ❌ 缺失 | 首見 2026-05-06，已追蹤 |
| 計時器倒數 | 顯示 | ✅ 05 | ✅ 實作 | |
| 標記複習 | 按鈕 | ✅ 05 | ✅ 實作 | |
| 題目導航格 | 互動 | ✅ 05 | ✅ 實作 | |
| 提交按鈕 | 按鈕 | ✅ 05 | ✅ 實作 | |
| Certi 打氣 Banner | 顯示 | ✅ 05 | ✅ 實作 | |
| AI Inference 判斷（保留/採信/略過） | 按鈕 | 🔴 無 Feature Scenario | ✅ 實作 | 首見 2026-05-06，已追蹤 |

---

### /exam/results — 測驗結果

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 成績卡（分數、合格與否、Confetti） | 顯示 | ✅ 06 | ✅ 實作 | |
| 知識節點答對率（三色標示） | 顯示 | ✅ 06、27 | ✅ 實作 | |
| AI 考後總評（FREE tier 付費牆） | 顯示 | ✅ 06 | ✅ 實作 | |
| 信心度四象限分析 | 顯示 | ✅ 20 | ✅ 實作 | |
| 交錯練習模式標籤 | 顯示 | ✅ 19 | ✅ 實作 | |
| 進入錯題本（AI 解析）按鈕 | 連結 | ✅ 07 | ✅ 實作 | |
| 逐題解析（含答對題）按鈕 | 連結 | ✅ 06 | ✅ 實作 | |
| 徽章分享（ShareBadgeModal）按鈕 | 按鈕 | ✅ 06 | ✅ 實作 | |
| ForceGraph 知識圖譜 | 顯示 | ✅ 03 | ✅ 實作 | |

---

### /practice — 自由練習

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 知識節點選擇列表 | 互動 | ✅ 32 | ✅ 實作 | |
| 答題區（選項、提交） | 互動 | ✅ 32 | ✅ 實作 | |
| 信心度校準 | 按鈕 | ✅ 20 | ✅ 實作 | |
| 即時回饋（正確/錯誤 + 詳解） | 顯示 | ✅ 32 | ✅ 實作 | |
| 階層回溯建議 banner（Feature 28） | 顯示 | ✅ 28 | ✅ 實作 | |
| 切換至父節點按鈕 | 按鈕 | ✅ 28 | ✅ 實作 | |
| 無題目空態 + Layer 3 job 查詢 | 顯示 | ✅ CLAUDE.md | ✅ 實作 | |
| 「選擇其他節點」+ 「回知識圖譜」按鈕 | 按鈕 | ✅ 32 | ✅ 實作 | |

---

### /review — 錯題複習與 AI 教練

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 錯題列表（側欄） | 顯示 | ✅ 07 | ✅ 實作 | |
| 逐題詳解（含 AI 解析） | 顯示 | ✅ 07 | ✅ 實作 | |
| AI 教練對話 | 互動 | ✅ 07 | ✅ 實作 | |
| 引用來源展開 | 按鈕 | ✅ 07 | ✅ 實作 | |
| 創建錯題專項測驗按鈕 | 按鈕 | ✅ 07 | ✅ 實作 | |
| FREE 毛玻璃升級攔截 | 顯示 | ✅ 07 | ✅ 實作 | |
| 空態 Layer 3（查最近失敗測驗） | 顯示 | ✅ CLAUDE.md | ✅ 實作 | |
| KaTeX 數學公式渲染 | 顯示 | ✅ 07 | ✅ 實作 | |

---

### /schedule — 學習排程

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 各科排程卡片（含模式 badge） | 顯示 | ✅ 09 | ✅ 實作 | |
| 距考日天數 + 推薦題數 | 顯示 | ✅ 09 | ✅ 實作 | |
| 「一鍵複習」按鈕（→ /exam/setup） | 連結 | ✅ 09 | ✅ 實作 | |
| 無科目空態引導（→ /onboarding） | 顯示 | ✅ 09 | ✅ 實作 | |
| 到期複習提醒連結（→ /review） | 連結 | ✅ 09 | ✅ 實作 | |

---

### /login — 身分驗證

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email 輸入 | 輸入 | ✅ 01 | ✅ 實作 | |
| 密碼輸入（顯示/隱藏） | 輸入 | ✅ 01 | ✅ 實作 | |
| Remember Me 勾選 | 互動 | ✅ 01 | ✅ 實作 | |
| Email 登入按鈕 | 按鈕 | ✅ 01 | ✅ 實作 | |
| Google SSO 按鈕 | 按鈕 | ✅ 01 | ✅ 實作 | |
| 忘記密碼連結 | 連結 | ✅ 01 | ✅ 實作 | |
| 前往註冊連結 | 連結 | ✅ 01 | ✅ 實作 | |
| 錯誤訊息顯示 | 顯示 | ✅ 01 | ✅ 實作 | |

---

### /signup — 註冊

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 名稱/Email/密碼輸入 | 輸入 | ✅ 01 | ✅ 實作 | |
| 同意條款勾選 | 互動 | ✅ 01 | ✅ 實作 | |
| 服務條款 modal | 按鈕 | ✅ 01 | ✅ 實作 | |
| 隱私政策 modal | 按鈕 | ✅ 01 | ✅ 實作 | |
| 密碼強度指示條 | 顯示 | ✅ 01 | ✅ 實作 | |
| 提交按鈕 | 按鈕 | ✅ 01 | ✅ 實作 | |
| 錯誤訊息顯示 | 顯示 | ✅ 01 | ✅ 實作 | |

---

### /onboarding — 首次引導

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 多步驟引導流程 | 互動 | ✅ 15 | ✅ 實作 | |
| 上一步/下一步按鈕 | 按鈕 | ✅ 15 | ✅ 實作 | |
| 驗證錯誤提示 | 顯示 | ✅ 15 | ✅ 實作 | |

---

### /account — 帳號設定

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 個人資料 Tab（姓名/年齡/職業/學歷） | 互動 | ✅ 22 | ✅ 實作 | |
| 訂閱與帳單 Tab | 顯示 | ✅ 08 | ✅ 實作 | |
| 安全 Tab（密碼變更/刪除帳號） | 互動 | ✅ 22 | ✅ 實作 | |
| 偏好設定 Tab（通知/深色模式/語言） | 互動 | ✅ 22 | ✅ 實作 | |
| 番茄鐘偏好設定 | 互動 | 🔴 Feature 21 有 Scenario | ❌ 缺失 | 首見 2026-05-06，已追蹤 |
| 成就系統 Tab | 顯示 | ✅ 13 | ✅ 實作 | |

---

### /account/my-subjects — 我的科目

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 科目列表 | 顯示 | ✅ 13 | ✅ 實作 | |
| 刪除科目按鈕（含確認） | 按鈕 | ✅ 13、35 | ✅ 實作 | |
| 錯誤態顯示 | 顯示 | ✅ | ✅ 實作 | |

---

### /account/weekly-reports — 歷史週報

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 週報列表 | 顯示 | ✅ 14 | ✅ 實作 | |
| 手動觸發週報按鈕 | 按鈕 | ✅ 14 | ✅ 實作 | |
| 空態說明文字（尚無週報） | 顯示 | 🔴 Feature 14 未覆蓋 | ✅ 有文字 | 首見 2026-05-06，已追蹤 |

---

### /pricing — 定價頁

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 方案卡片（FREE/PRO/PRO_PLUS/ULTRA） | 顯示 | ✅ 18 | ✅ 實作 | |
| 方案選擇按鈕 | 按鈕 | ✅ 18 | ✅ 實作 | |
| 試用期按鈕 | 按鈕 | ✅ 18 | ✅ 實作 | |

---

### /feedback — 意見反饋

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 反饋類型選擇 | 按鈕 | ✅ 17 | ✅ 實作 | |
| 標題/內容輸入 | 輸入 | ✅ 17 | ✅ 實作 | |
| 附件上傳 | 互動 | ✅ 17 | ✅ 實作 | |
| 提交按鈕 | 按鈕 | ✅ 17 | ✅ 實作 | |
| 我的反饋列表 | 顯示 | ✅ 17 | ✅ 實作 | |
| 提交成功狀態 + 重新填寫 | 顯示 | ✅ 17 | ✅ 實作 | |

---

### /forgot-password / /reset-password — 密碼重設流程

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| Email 輸入 + 發送按鈕 | 互動 | ✅ 01 | ✅ 實作 | |
| 發送成功狀態 | 顯示 | ✅ 01 | ✅ 實作 | |
| 新密碼 + 確認密碼輸入 | 輸入 | ✅ 01 | ✅ 實作 | |
| 錯誤顯示（token 過期等） | 顯示 | ✅ 01 | ✅ 實作 | |

---

### /verify-email / /verify-email/sent — 信箱驗證

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 驗證狀態（loading/success/error） | 顯示 | ✅ 01 | ✅ 實作 | |
| 重新寄送按鈕（cooldown + 錯誤提示） | 按鈕 | ✅ 01 | ✅ 實作 | |

---

### /edu-console — B2B 機構管理

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| DPA 簽署 Modal | 互動 | ✅ 10 | ✅ 實作 | |
| DPA 未簽置頂 Banner | 顯示 | ✅ 10 | ✅ 實作 | |
| CSV 匯入學員按鈕 | 按鈕 | ✅ 10 | ✅ 實作 | |
| 學員列表 | 顯示 | ✅ 10 | ✅ 實作 | |
| 空態「邀請第一位學員」CTA | 按鈕 | ✅ 10 | ✅ 實作 | |
| 資源管理（上傳/分享） | 互動 | ✅ 10 | ✅ 實作 | |

---

### /resources/[id]/candidates — 題目候選審核

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| 候選題目列表 + 勾選 | 互動 | ✅ 23 | ✅ 實作 | stub → client.tsx |
| 批量核准/拒絕按鈕 | 按鈕 | ✅ 23 | ✅ 實作 | |

---

### /invite/setup-password — 邀請設密碼

| 元素 | 類型 | Feature 覆蓋 | 實作狀態 | 備註 |
|------|------|-------------|---------|------|
| invite token 狀態（有效/過期/已用） | 顯示 | ✅ 10 | ✅ 實作 | |
| 密碼輸入 + 提交 | 互動 | ✅ 10 | ✅ 實作 | |
| 過期/錯誤引導（聯繫管理員） | 顯示 | ✅ 10 | ✅ 實作 | |

---

### /super-admin/* — 平台管理後台（彙整）

| 頁面 | 核心元素 | Feature 覆蓋 | 狀態 | 備註 |
|------|---------|-------------|------|------|
| /super-admin/dashboard | 系統 KPI、Alert 列表、刷新 | ✅ 12 | ✅ | |
| /super-admin/users | 使用者列表、搜尋過濾、分頁、停權 | ✅ 12 | ✅ | |
| /super-admin/users/[userId] | 詳情（stub → client.tsx） | ✅ 12 | ✅ | |
| /super-admin/finance | MRR 趨勢、退款、優惠碼 | ✅ 12a | ✅ | |
| /super-admin/moderation | 審核佇列、意見反饋、AI 濫用 | ✅ 12b | ✅ | |
| /super-admin/cost-monitor | GCP 成本、預算上限 | ✅ 33 | ✅ | `isAdmin` 守衛，應改 `isSuperAdmin` |
| /super-admin/audit-logs | 日誌列表、Export | ✅ 12 | ✅ | |
| /super-admin/anomaly | 異常清單、批次修復 | ✅ 16 | ✅ | |
| /super-admin/exam-import | 考古題匯入監控 | ✅ 23、32b | ✅ | |
| /super-admin/default-resources | 預設資源綁定 | ✅ 34 | ✅ | |
| /super-admin/platform-subjects | 平台科目管理、Fork | ✅ 12c、26、29、34 | ✅ | |
| /super-admin/prompt-templates | Prompt 模板列表 | ✅ 30 | ✅ | `isAdmin` 守衛，應改 `isSuperAdmin` |
| /super-admin/prompt-templates/new | 新增 Prompt 模板 | ✅ 30 | ✅ | |
| /super-admin/prompt-templates/[id] | 編輯（stub → client.tsx） | ✅ 30 | ✅ | |
| /super-admin/retirement | 退役題庫批次任務 | ✅ 25 | ✅ | |
| /super-admin/settings | AI 模型路由 | ✅ 12c | ✅ | `isAdmin` 守衛，應改 `isSuperAdmin` |
| /super-admin/settings/admins | 管理員帳號 | ✅ 12c | ✅ | |
| /super-admin/settings/announcements | 公告管理 | ✅ 24 | ✅ | |
| /super-admin/settings/flags | Feature Flags | ✅ 12c | ✅ | `isAdmin` 守衛，應改 `isSuperAdmin` |
| /super-admin/settings/plans | 方案配額 | ✅ 12c | ✅ | `isAdmin` 守衛，應改 `isSuperAdmin` |
| /super-admin/settings/api-keys | API Key 監控 | ✅ 12c | ✅ | |
| /super-admin/settings/version | 版本資訊 | ✅ 12c | ✅ | |

---

### 其他頁面

| 頁面 | 狀態 | 備註 |
|------|------|------|
| / (landing) | ✅ 正常 | 行銷頁，無 BDD 對應 |
| /radar-demo | ✅ isSuperAdmin 守衛已加 | 修復：2026-05-06 |
| /edu-console/student/[id] | ✅ stub 正常 | Firebase rewrite 處理 |

---

## Feature File 覆蓋摘要

| Feature File | 對應頁面 | @wip 數 | 備註 |
|-------------|---------|--------|------|
| 01-身分驗證 | /login, /signup | 0 | |
| 02-資源上傳 | /dashboard | 2 | GCS 前綴、BackgroundTasks RLS（@wip） |
| 03-知識心智圖 | /knowledge | 0 | 🔴 搜尋節點篩選 Scenario 實作不符 |
| 03a-知識心智圖生成 | /knowledge | 0 | |
| 03b-知識心智圖導航 | /knowledge, /knowledge/mindmap | 0 | |
| 04-測驗設定 | /exam/setup | 0 | |
| 04a-AI考題生成服務 | /exam/setup | 0 | |
| 05-模擬機考 | /exam/workspace | 0 | |
| 06-測驗結果 | /exam/results | 0 | |
| 07-錯題複習與AI教練 | /review | 0 | |
| 08-訂閱管理 | /account | 0 | |
| 08a-綠界金流串接 | /account | 0 | |
| 08b-付款後權限更新 | /account | 0 | |
| 09-學習記憶排程 | /schedule | 0 | |
| 10-B2B機構管理後台 | /edu-console | 0 | |
| 11-資源庫管理 | /knowledge | 0 | |
| 12-平台管理後台 | /super-admin/* | 0 | |
| 12a-財務管理 | /super-admin/finance | 0 | |
| 12b-內容審核 | /super-admin/moderation | 0 | |
| 12c-系統設定 | /super-admin/settings/* | 0 | |
| 13-個人儀表板與成就系統 | /dashboard | 0 | 🔴 科目切換器 Scenario 未同步移除 |
| 14-社群歸屬與主動關懷 | /account/weekly-reports | 0 | |
| 15-首次登入引導 | /onboarding | 1 | BackgroundTasks RLS @wip |
| 16-異常維修管理 | /super-admin/anomaly | 0 | |
| 17-意見反饋 | /feedback | 0 | |
| 18-定價與升級引導 | /pricing | 0 | |
| 18-題目分類與考試趨勢分析 | /exam/results（Bloom） | 0 | @backend only |
| 19-交錯練習 | /exam/setup | 0 | |
| 20-信心度校準 | /exam/workspace, /exam/results | 0 | |
| 21-番茄鐘學習節奏 | /exam/workspace | 0 | 設定 UI 缺失已追蹤 |
| 22-帳號設定與個人偏好 | /account | 0 | |
| 23-考古題題庫管理 | /super-admin/exam-import, /resources/[id]/candidates | 1 | scope=personal @wip |
| 24-系統公告管理 | /super-admin/settings/announcements | 0 | |
| 25-AI考題退場與放榜確認 | /super-admin/retirement, /dashboard | 0 | |
| 26-考綱逆向工程 | 後端自動觸發（UI 已移除） | 0 | 設計決策，非問題 |
| 27-個人化錯題地圖 | /knowledge/wrong-answers | 0 | |
| 28-階層式難度遞進 | /practice | 0 | |
| 29-知識樹合併對齊 | /super-admin/platform-subjects | 0 | |
| 30-Prompt模板管理 | /super-admin/prompt-templates/* | 0 | |
| 31-多租戶安全與資料隔離 | 後端+DB | 2 | NULL tenant_id @wip |
| 32-節點練習模式 | /practice | 0 | |
| 32-考古題現代化匯入 | /super-admin/exam-import | 0 | |
| 33-成本監控中心 | /super-admin/cost-monitor | 0 | |
| 34-預載科目Fork | /super-admin/platform-subjects | 0 | |
| 35-科目硬刪除 | /account/my-subjects | 0 | |
| 36-資源硬刪除 | /knowledge | 0 | |

---

## 問題彙整（今日新增）

### 🔴 Feature 缺失（需同步更新 Feature Spec）

1. `/dashboard` — Feature 13（L40-58）仍保有 2 個 active Example Scenario 要求 dashboard 顯示科目切換器（「備考多科時顯示科目切換器應包含 AWS SAA、TOEIC」、「切換科目後儀表板數據更新」）。但 SubjectSwitcher 已於 2026-05 從 dashboard 移除（多科切換改至 /knowledge 和 /onboarding）。Feature 13 相關 Scenario 未同步移除或改寫，若跑前端 BDD 必然失敗。需在 Feature 13 中將科目切換器 Rule 改寫為描述 ScheduleWeekCard 替代行為，或新增「@removed 2026-05」標記。

2. `/knowledge` — Feature 03 Rule「搜尋知識點可即時篩選心智圖導覽區的節點」Example「右側心智圖導覽區應僅顯示包含 'S3' 關鍵字的知識節點」。目前前端搜尋框只過濾左側文件列表，ForceGraph/MindMapTree 節點不受搜尋詞影響。需補前端實作（將 searchQuery 傳入 MindMapTree/ForceGraph）或更新 Feature 03 Scenario 範圍。

### 🟠 實作缺失（Feature 存在但頁面缺功能）

1. `/knowledge` — 搜尋框（searchQuery state，knowledge/page.tsx L614）只用於過濾文件列表，未將搜尋詞傳遞給 MindMapTree 或 ForceGraph 元件進行節點過濾。Feature 03 Scenario 期待「心智圖導覽區節點可依關鍵字即時篩選」，實際行為不符。

### 🟡 空態補強（前次修復未達完整 Layer 3 標準）

1. `/exam/setup` — documents.length === 0（COMPLETED 文件為空）時顯示靜態文字「若已上傳資源但此處為空，可能資源解析失敗，請至知識庫頁面查看狀態」（L609-615）。未主動呼叫 `resourceParseService.getStatus()` 查詢 parse job failure_reason，用戶須手動跳轉至 /knowledge 才能看到具體失敗原因。依 CLAUDE.md Layer 3 標準，空態應直接查 job 表呈現具體失敗原因於當頁。前次（2026-04-24）標記為已修復，但實際只達到「靜態提示」層級，未達 Layer 3 主動查 job 表標準。

---

## 既有追蹤問題確認（詳見 ToDoList.md 2026-05-06 條目）

以下問題已於 2026-05-06 首見並追蹤，本次審查確認仍未修復：

- 🔴 `/exam/workspace` + `/practice` — AI inference 判斷按鈕無 Feature Scenario
- 🔴 `/dashboard` — 模式 tooltip 說明按鈕無 Feature Scenario  
- 🔴 `/dashboard` — 無科目時 dashboard-level modal 路徑無 Feature Scenario
- 🔴 `/account/weekly-reports` — Feature 14 未覆蓋空態 UI 情境
- 🟠 `/exam/workspace` — Feature 21 番茄鐘啟用開關、時長設定、繼續作答/開始休息 UI 缺失
- 🟠 `/knowledge` — Feature 03 節點掌握時 Confetti/獎章動畫缺實作
- 🟡 `/dashboard` — 上傳失敗後未查 resource_parse_jobs.failure_reason
- 🟡 `/knowledge` — PROCESSING 狀態資源未向用戶顯示進度說明

---

*本報告由 TiTi QA 架構師排程任務自動產出，每日覆蓋寫入。*
