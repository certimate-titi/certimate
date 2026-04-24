# CertiMate ToDoList
**最後更新**：2026-04-24

---

## 🔴 Feature 缺失 — 需補 Gherkin Scenario

- [ ] `/dashboard` — 科目切換器 (SubjectSwitcher) 缺 Feature Scenario（Feature 13 全 35 個 @ignore 需解封或重寫）（首見：2026-04-24）
- [ ] `/dashboard` — 複習日曆 + 月份切換缺 Feature Scenario（Feature 13 全 @ignore）（首見：2026-04-24）
- [ ] `/dashboard` — 每日任務 (DailyQuestCard) 缺 Feature Scenario（Feature 13 全 @ignore）（首見：2026-04-24）
- [ ] `/dashboard` — 備考模式標籤 Sprint/Standard/Mastery 無任何 Feature 覆蓋（首見：2026-04-24）
- [ ] `/dashboard` — 核心指標卡（streak、答題數、答對率、預測及格率）缺 Feature Scenario（首見：2026-04-24）
- [ ] `/knowledge` — 科目切換器無 active Scenario（Feature 03 全 @ignore）（首見：2026-04-24）
- [ ] `/knowledge/mindmap` — ForceGraph/MindMapTree 視圖切換無任何 Feature 覆蓋（首見：2026-04-24）
- [ ] `/exam/results` — 成績卡片下載按鈕無 Feature Scenario（功能目前為 stub）（首見：2026-04-24）
- [ ] `/exam/workspace` — 番茄鐘計時器 Feature 21 存在但 0 active Scenario，疑似頁面未完整實作（首見：2026-04-24）
- [ ] `/account/my-subjects` — 刪除科目功能無任何 Feature 覆蓋（首見：2026-04-24）
- [ ] `/account/resource-library` — 資源分享功能無 active Feature Scenario（Feature 11 @wip）（首見：2026-04-24）
- [ ] `/library` — Tab 切換無任何 Feature 覆蓋（首見：2026-04-24）
- [ ] `/edu-console` — CSV 匯入 / 新增學員 Feature 10 全 @ignore，無 active Scenario（首見：2026-04-24）
- [ ] `/super-admin/settings/flags` — Feature Flag 設定無任何 Feature 覆蓋（首見：2026-04-24）
- [ ] `/super-admin/settings/plans` — 方案配額管理無 active Feature Scenario（首見：2026-04-24）
- [ ] `/super-admin/users/[userId]` — 用戶詳情頁無 active Feature Scenario（首見：2026-04-24）
- [x] `19-交錯練習.feature` + `32-節點練習模式.feature` + `46-知識地圖Canvas.feature` — ~~Feature 檔案存在但 Scenario 數量為 0~~ **已有完整 Scenario**（19：8 Examples, 32：9 Examples, 46：6 Examples）（確認：2026-04-24 自動巡檢）

---

## 🟠 實作缺失 — 需補前端功能

- [ ] `/exam/results` — Feature 06 描述「逐題解析」查看，但頁面無跳轉逐題解析的按鈕或入口（首見：2026-04-24）
- [ ] `/exam/results` — 成績卡片下載按鈕功能為 alert stub（`"即將推出"`），需實作實際下載功能（首見：2026-04-24）
- [ ] `/exam/workspace` — Feature 21（番茄鐘）存在，但頁面無 pomodoro/番茄鐘相關實作邏輯，需確認並實作（首見：2026-04-24）
- [ ] `/knowledge` — Feature 46（知識地圖 Canvas 三層 Zoom）存在，頁面使用 ForceGraph 但三層 Zoom 邏輯未明確實作，需對照 PRD-046（首見：2026-04-24）
- [x] `/practice` — no-questions 空態已新增「前往出題」快捷按鈕（自動帶入當前 nodeId），引導至 `/exam/setup`（修復：2026-04-24 自動巡檢）
- [ ] `/super-admin/anomaly` — Feature 16「批次修復」情境缺乏對應 UI 元素與 Scenario 覆蓋（首見：2026-04-24）

---

## 🟡 空態補強 — 需查 Job 表

- [x] `/knowledge` — documents.length === 0 空態已區分「從未上傳」；FAILED 文件自動查詢 `resource_parse_jobs.failure_reason` 並顯示（修復：2026-04-24 自動巡檢）
- [x] `/knowledge/mindmap` — mindMapNodes.length === 0 空態已根據文件狀態區分四種情境：無資源/全部失敗/處理中/未萃取（修復：2026-04-24 自動巡檢）
- [x] `/practice` — phase === 'no-questions' 空態已新增提示訊息（AI 出題可能失敗）及「前往出題」快捷按鈕（修復：2026-04-24 自動巡檢）
- [x] `/exam/setup` — documents.length === 0 空態已新增提示：若已上傳資源但為空，引導至知識庫查看解析狀態（修復：2026-04-24 自動巡檢）
- [ ] `/library` — 頁面空態情況不明，建議確認 Tab 切換後空態是否查詢相關 job 狀態（首見：2026-04-24）

---

## ✅ 已完成

（無已完成項目，新建立清單）
