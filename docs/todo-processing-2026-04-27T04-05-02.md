# ToDoList 自動巡檢紀錄 — 2026-04-27T04:05 (UTC+8)

**觸發方式**：排程自動巡檢（check-todo）
**執行者**：TiTi Commander 自動巡檢模式

---

## 巡檢摘要

本次巡檢對 `docs/ToDoList.md` 中所有未完成的待辦事項進行 Feature 檔案狀態驗證。
發現 **14 項** 先前標記為未完成的項目實際上已有對應的 Feature Scenario 覆蓋，可標記為已完成。

---

## 🔴 Feature 缺失 — 狀態更新

### 已解決（本次確認）

| # | 項目 | 驗證結果 | 依據 |
|---|------|---------|------|
| 1 | `/dashboard` — 科目切換器 SubjectSwitcher | ✅ 已有 Scenario | Feature 13 共 36 個 active Example（0 @ignore），Rule「儀表板應顯示科目切換器」(L40) |
| 2 | `/dashboard` — 複習日曆 + 月份切換 | ✅ 已有 Scenario | Feature 13 Rule「艾賓浩斯複習月曆」(L250)，含月份參數 "2026-04" |
| 3 | `/dashboard` — 每日任務 DailyQuestCard | ✅ 已有 Scenario | Feature 13 Rule「每日首次登入應自動產生 1-3 個微任務」(L96)，含任務完成觸發 (L108) |
| 4 | `/dashboard` — 核心指標卡（streak、答題數等） | ✅ 已有 Scenario | Feature 13 Rule「每日登入並學習應累積連勝天數」(L73)，含 streak_7 欄位驗證 |
| 5 | `/dashboard` — 待辦提醒 activityItems | ✅ 已有 Scenario | Feature 13 Rule「儀表板應包含考試倒數、雷達圖、快速上傳區與待辦提醒」(L59) |
| 6 | `/dashboard` — DomainRadarChart 領域雷達圖 | ✅ 已有 Scenario | Feature 13 Rule「雷達圖應顯示各領域的強度資料」(L228)，含能力分布驗證 |
| 7 | `/edu-console` — CSV 匯入 / 新增學員 | ✅ 已有 Scenario | Feature 10 共 55 個 active Example（@command 非 @ignore），含 CSV 匯入、DPA 簽署等 |
| 8 | `/account/my-subjects` — 刪除科目功能 | ✅ 已有 Scenario + 前端實作 | Feature 13 Rule「帳戶頁面科目編輯與移除」(L357)，前端 handleDelete 已實作 |
| 9 | `/super-admin/audit-logs` — 審計日誌 | ✅ 已有 Scenario | Feature 12 共 35 個 active Example（0 @ignore），含 10 處審計日誌記錄驗證 |
| 10 | `/super-admin/retirement` — AI 考題退場 | ✅ 已有 Scenario | Feature 25 共 36 個 active Example（0 @ignore/@skip），涵蓋來源標記、品質管理、退場流程 |
| 11 | `/super-admin/default-resources` — 預設資源 Fork | ✅ 已有 Scenario | Feature 34 共 9 個 active 場景，含 fork、冪等性、atomicity 等 |
| 12 | `/super-admin/settings/flags` — Feature Flag | ✅ 已有 Scenario | Feature 12c Rule「更新 Feature Flag 上線比例」+ Rule「Feature Flag 應支援切換開關操作」 |
| 13 | `/super-admin/settings/plans` — 方案配額管理 | ✅ 已有 Scenario | Feature 12c Rule「方案配額表格應支援行內編輯與儲存」 |
| 14 | `/super-admin/users/[userId]` — 用戶詳情頁 | ✅ 已有 Scenario | Feature 12 Rule「用戶詳情頁應回傳六個資訊區塊」 |

### 仍未解決

| # | 項目 | 狀態 | 說明 |
|---|------|------|------|
| 1 | `/dashboard` — 備考模式標籤 Sprint/Standard/Mastery | ❌ 仍無覆蓋 | Feature 13 中無任何 Sprint/Standard/Mastery 相關 Scenario |
| 2 | `/knowledge/mindmap` — ForceGraph/MindMapTree 視圖切換 | ❌ 仍無覆蓋 | Feature 03/03b/46 均未提及視圖切換 |
| 3 | `/exam/results` — 成績卡片下載按鈕 | ❌ 仍無覆蓋 | 功能仍為 stub |
| 4 | `/library` — Tab 切換 | ❌ 仍無覆蓋 | Feature 11 無 Tab 切換 Scenario |
| 5 | `/super-admin/settings/version` — 版本資訊頁 | ❌ 仍無覆蓋 | Feature 12c 未涵蓋版本資訊頁 |
| 6 | `/dashboard` — StudyBuddyBanner ULTRA 共讀橫幅 | ❌ 仍無覆蓋 | Feature 13 無任何 StudyBuddy 相關 Scenario |
| 7 | `/super-admin/platform-subjects` — 平台科目管理 | ❌ 仍無覆蓋 | Feature 34 僅涵蓋 fork，未涵蓋平台科目 CRUD |
| 8 | `/resources/[id]/candidates` — 候選考題管理 | ❌ 仍無覆蓋 | 無任何 Feature 對應此路徑 |

---

## 🟠 實作缺失 — 狀態（未變更）

以下項目本次未進行程式碼修改，保持原狀：

- `/exam/results` — 逐題解析入口（仍缺）
- `/exam/results` — 成績卡片下載 stub（仍為 alert）
- `/exam/workspace` — 番茄鐘（Feature 存在但前端未實作）
- `/knowledge` — 三層 Zoom（前端未明確實作）
- `/super-admin/anomaly` — 批次修復 UI（仍缺）

---

## 🟡 空態補強 — 狀態（未變更）

- `/library` — 空態未確認
- `/practice` — 未實際查詢 resource_parse_jobs（仍僅文字引導）

---

## 執行動作

1. ✅ 更新 `docs/ToDoList.md` — 標記 14 項已解決
2. ✅ 產出本紀錄檔 `docs/todo-processing-2026-04-27T04-05-02.md`
3. ✅ Git commit: `d718fc0` — `chore(docs): 自動巡檢更新 ToDoList — 14 項 Feature 缺失確認已解決`
4. ⚠️ Git push 失敗（sandbox 無 GitHub 認證），需手動執行 `git push origin main`
