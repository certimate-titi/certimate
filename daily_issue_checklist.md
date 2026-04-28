# CertiMate Daily QA Issue Checklist

**產出時間**：2026-04-28（自動排程 daily-qa-page-audit）
**審查頁面數**：48 頁（frontend/app/ 全部 page.tsx）
**Feature File 數**：46 個（project/features/ 全部 .feature）
**發現問題總計（本次新增）**：🔴 1 + 🟠 2 + 🟡 1
**累積未解決問題**：🔴 9 + 🟠 7 + 🟡 3

---

## 本次新發現問題（2026-04-28 首見）

### 🔴 Feature 缺失

**N1 — `/exam/setup`**：Feature 19（交錯練習）明確規定測驗設定頁應讓用戶選擇題目**排列模式**（interleaved / grouped / sequential），但 `exam/setup/page.tsx` 目前無此 UI 選項。頁面有 `TIER_QUESTION_LIMITS`、難易度滑桿、AI hybrid / historical_only 切換，唯獨缺排列模式選擇器。Feature 19 的 Scenario 亦無對應前端驗收測試。

### 🟠 實作缺失

**N2 — `/review` KaTeX 聲稱支援但無 import**：`review/page.tsx` 第 459 行顯示 disclaimer「支援 KaTeX 數學公式渲染」，但整個 page.tsx 無任何 `katex`、`react-katex`、`remark-math` 等相關套件 import。Feature 07 亦無對應 Scenario 驗證數學公式渲染。屬虛假宣稱，需補實作或移除 disclaimer。

**N3 — `/knowledge` 新增資源導航行為 Feature 未覆蓋**：知識心智圖頁的「+ 新增資源」按鈕點擊後路由至 `/dashboard`（跨頁面導航），而非直接開啟上傳 modal。此互動路徑在 Feature 03（知識心智圖）中無 Scenario 覆蓋，若導航目標變更將無回歸測試保護。

### 🟡 空態補強

**N4 — `/review` 全答對空態未查 Job Table**：`wrongQuestions.length === 0` 時直接顯示「全部答對！」，但未查詢後端 `exam_generation_jobs` 或 `resource_parse_jobs` 確認近期是否有 FAILED job。違反 Layer 3 規則（參照 2026-04-23 空態誤判事件）。

---

## 所有未解決問題彙整（截至 2026-04-28）

### 🔴 Feature 缺失（共 9 項）

| 狀態 | 路由 | 問題描述 | 首見 |
|------|------|----------|------|
| `[ ]` | `/exam/setup` | Feature 19 排列模式（interleaved/grouped/sequential）UI 完全缺失 | **2026-04-28** |
| `[ ]` | `/dashboard` | 備考模式標籤 Sprint/Standard/Mastery 無任何 Feature 覆蓋 | 2026-04-24 |
| `[ ]` | `/dashboard` | StudyBuddyBanner（ULTRA 共讀橫幅）無任何 Feature 覆蓋 | 2026-04-27 |
| `[ ]` | `/knowledge/mindmap` | ForceGraph/MindMapTree 視圖切換無任何 Feature 覆蓋 | 2026-04-24 |
| `[ ]` | `/exam/results` | 成績卡片下載按鈕無 Feature Scenario（功能目前為 stub） | 2026-04-24 |
| `[ ]` | `/library` | Tab 切換（我的素材 / 知識地圖）無任何 Feature 覆蓋 | 2026-04-24 |
| `[ ]` | `/super-admin/settings/version` | 版本資訊頁無任何 Feature 覆蓋 | 2026-04-24 |
| `[ ]` | `/super-admin/platform-subjects` | 平台科目管理無任何 Feature 覆蓋 | 2026-04-27 |
| `[ ]` | `/resources/[id]/candidates` | 候選考題管理頁面無任何 Feature 覆蓋（Feature 23/25 未對應此路由） | 2026-04-27 |

### 🟠 實作缺失（共 7 項）

| 狀態 | 路由 | 問題描述 | 首見 |
|------|------|----------|------|
| `[ ]` | `/review` | 聲稱支援 KaTeX 數學公式渲染但無任何套件 import；Feature 07 無對應 Scenario | **2026-04-28** |
| `[ ]` | `/knowledge` | 「+ 新增資源」跨頁面導航（→ /dashboard）Feature 03 無對應 Scenario 覆蓋 | **2026-04-28** |
| `[ ]` | `/exam/results` | Feature 06 描述「逐題解析」查看，頁面無任何入口或按鈕 | 2026-04-24 |
| `[ ]` | `/exam/results` | 成績卡片下載為 `alert('即將推出')` stub，需實作實際下載功能 | 2026-04-24 |
| `[ ]` | `/exam/workspace` | Feature 21（番茄鐘）有 15 個 active Scenario，頁面無任何 Pomodoro 計時器實作 | 2026-04-24 |
| `[ ]` | `/knowledge` | Feature 46（知識地圖 Canvas 三層 Zoom）頁面用 ForceGraph 但三層 Zoom 邏輯未明確實作 | 2026-04-24 |
| `[ ]` | `/super-admin/anomaly` | Feature 16「批次修復」情境缺乏對應 UI 元素與 Scenario 覆蓋 | 2026-04-24 |

### 🟡 空態補強（共 3 項）

| 狀態 | 路由 | 問題描述 | 首見 |
|------|------|----------|------|
| `[ ]` | `/review` | `wrongQuestions.length === 0` 空態（「全部答對！」）未查詢 job 表確認是否真空 | **2026-04-28** |
| `[ ]` | `/practice` | `no-questions` 空態有文字 hint 但未實際查詢 `resource_parse_jobs.failure_reason` | 2026-04-24 |
| `[ ]` | `/library` | Tab 切換後空態情況不明，未確認是否查詢 job 表 | 2026-04-24 |

---

## 已確認正常（Layer C 通過）

| 路由 | Layer 3 狀態 | 確認日期 |
|------|-------------|----------|
| `/knowledge` | FAILED 文件查詢 `resource_parse_jobs.failure_reason` ✅；PROCESSING 文件每 5s 輪詢 ✅ | 2026-04-24 |
| `/knowledge/mindmap` | 空態區分四情境（無資源 / 全失敗 / 處理中 / 未萃取）✅ | 2026-04-24 |
| `/account/resource-library` | FAILED 資源 failure_reason 透過 hover tooltip 顯示 ✅ | 2026-04-25 |
| `/exam/setup` | 空文件清單時有引導提示至知識庫查看解析狀態 ✅ | 2026-04-24 |
| `/dashboard` | `subjectsLoaded` 旗標防止假空態 ✅ | 2026-04-27 |

---

## 頁面審查摘要（Layer A + B）

| 路由 | Feature 覆蓋 | 實作完整性 | 問題 |
|------|-------------|-----------|------|
| `/dashboard` | ⚠️ 部分缺 | ✅ 主功能完整 | 🔴×2（備考模式標籤、StudyBuddyBanner） |
| `/knowledge` | ⚠️ 部分缺 | ✅ 主功能完整 | 🟠×2（新增資源導航、Canvas 三層 Zoom） |
| `/knowledge/mindmap` | ❌ 視圖切換無覆蓋 | ✅ 主功能完整 | 🔴×1 |
| `/practice` | ✅ Feature 32 覆蓋 | ✅ 主功能完整 | 🟡×1（空態未查 job） |
| `/review` | ⚠️ 部分缺 | ⚠️ KaTeX 未實作 | 🟠×1、🟡×1 |
| `/exam/setup` | ⚠️ 缺排列模式 | ⚠️ 排列模式 UI 缺 | 🔴×1 |
| `/exam/workspace` | ⚠️ 缺 Pomodoro | ⚠️ 番茄鐘未實作 | 🟠×1 |
| `/exam/results` | ❌ 下載無覆蓋 | ⚠️ 下載/逐題解析 stub | 🔴×1、🟠×2 |
| `/library` | ❌ Tab 切換無覆蓋 | ✅ 主功能完整 | 🔴×1、🟡×1 |
| `/account` | ✅ Feature 22 覆蓋 | ✅ 完整 | — |
| `/account/my-subjects` | ✅ Feature 13 覆蓋 | ✅ 完整 | — |
| `/account/resource-library` | ✅ Feature 11 覆蓋 | ✅ 完整 | — |
| `/onboarding` | ✅ Feature 15 覆蓋 | ✅ 完整 | — |
| `/signup` | ✅ Feature 01 覆蓋 | ✅ 完整 | — |
| `/login` | ✅ Feature 01 覆蓋 | ✅ 完整 | — |
| `/verify-email` | ✅ Feature 01 覆蓋 | ✅ 完整 | — |
| `/pricing` | ✅ Feature 18 覆蓋 | ✅ 完整 | — |
| `/feedback` | ✅ Feature 17 覆蓋 | ✅ 完整 | — |
| `/edu-console` | ✅ Feature 10 覆蓋 | ✅ 完整 | — |
| `/super-admin/*` | ⚠️ 部分缺 | ✅ 主功能完整 | 🔴×2、🟠×1 |

---

## 違規歷史（QA 前車之鑑）

| 日期 | 事件 |
|------|------|
| 2026-04-13 | 前端練習頁 API 欄位 `name` vs 型別 `label` 不一致，節點名稱全空；QA 三輪退回 |
| 2026-04-23 | QA 判定「此資源尚無學習鷹架」為合理空態並簽核，實際 DB parse job 全部 `failed`；新增 Layer 3 空態必查 job 表規則 |
| 2026-04-27 | ForceGraph 規格毀損事件：跨 Feature 資料夾刪除 Scenario 前未確認對側 sibling 覆蓋 |

---

*本檔案由自動排程任務每日覆蓋產出，請勿手動修改。詳細追蹤請見 `docs/ToDoList.md`。*
