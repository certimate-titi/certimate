# TiTi Commander 排程巡檢紀錄 — 2026-05-05T04:06

> **觸發方式**：自動排程 (check-todo scheduled task)
> **執行者**：TiTi Commander v2.1

---

## 巡檢結果摘要

掃描 `docs/ToDoList.md`，發現 **4 個未完成待辦事項**（🔴3 + 🟡1 重複項），全部已處理完畢。

| # | 待辦 | 分類 | 處理方式 | 狀態 |
|---|------|------|----------|------|
| 1 | `/exam/results` 信心度四象限 UI | 🔴 Feature 缺失 | 新增前端元件 + service | ✅ 完成 |
| 2 | `/schedule` Feature 09 缺獨立 Scenario | 🔴 Feature 缺失 | 新增 Rule + 3 Examples | ✅ 完成 |
| 3 | Feature 18 Bloom 前端頁面確認 | 🔴 Feature 缺失 | CEO 決議標記 @backend | ✅ 完成 |
| 4 | `/knowledge/wrong-answers` 空態 Layer 3 | 🟡 空態補強 | 新增 useEffect + 條件 UI | ✅ 完成 |

---

## 詳細處理紀錄

### 1. `/exam/results` — 信心度四象限分析 UI（Feature 20）

**問題**：Feature 20 Rule (L59-83) 規定測驗結果頁應提供四象限統計（confident_correct / confident_incorrect / guessing_correct / guessing_incorrect），後端 API `GET /api/v1/exams/{exam_id}/confidence-analysis` 已完整實作，但前端 page.tsx 完全缺此區塊。

**修改檔案**：
- `frontend/lib/api/services.ts`：
  - 新增 `ConfidenceQuadrant` 與 `ConfidenceAnalysisResponse` 介面
  - examService 新增 `getConfidenceAnalysis(examId)` 方法
- `frontend/app/exam/results/page.tsx`：
  - 新增 `confidenceData` state
  - useEffect 中在取得 exam results 後非同步載入 confidence data
  - 新增「信心度四象限分析」區塊（data-testid="confidence-quadrant-analysis"）：
    - 2x2 象限卡片：真正掌握（emerald）、危險盲點（rose）、幸運猜對（amber）、預期弱點（slate）
    - 校準率（Calibration Rate）百分比進度條
    - AI Coach 紅色警示區塊（confident_incorrect > 0 時）
    - AI Coach 黃色提醒區塊（guessing_correct > 0 時）

**驗證**：TypeScript 編譯零錯誤（`npx tsc --noEmit`）

---

### 2. `/schedule` — Feature 09 補充完整排程頁 Scenario

**問題**：Feature 09 僅有儀表板 ScheduleWeekCard 入口的 2 個 Scenario，完整 `/schedule` 頁面（排程列表、各科模式卡片、開始今日複習按鈕）無獨立 Scenario 覆蓋。

**修改檔案**：
- `project/features/09-學習記憶排程.feature`：
  - 新增 Rule「完整排程頁展示各科學習建議與一鍵複習入口」
  - 3 個 @frontend Example Scenario：
    1. 各科排程卡片含模式 badge + 待複習題數 + 開始今日複習按鈕
    2. 距考日天數 + 推薦題數顯示
    3. 空態引導至 /onboarding

**備註**：/schedule page.tsx 已完整實作，此次僅補 Feature 規格。

---

### 3. Feature 18 — CEO 決議標記 @backend

**問題**：Feature 18（題目分類與考試趨勢分析）的 Bloom 分佈統計與年度考試趨勢分析被標記為 @frontend，但無對應前端頁面。

**分析**：
- 後端 API `GET /api/v1/subjects/{id}/bloom-distribution` 已存在（subjects.py + BloomAnalyticsService）
- 前端消費點為 `/exam/results` 頁的「Bloom 認知層次分析」區塊（已實作）
- 不需要獨立的前端分析頁面

**修改檔案**：
- `project/features/18-題目分類與考試趨勢分析.feature`：
  - Feature 標記從 `@frontend` 改為 `@backend`
  - 新增註解說明 CEO 決議及前端消費點

---

### 4. `/knowledge/wrong-answers` — Layer 3 空態查 Job 表

**問題**：`nodes.length === 0` 時直接顯示「尚無熱力圖資料」，未查詢 resource_parse_jobs 確認是否為解析失敗導致無知識節點。

**修改檔案**：
- `frontend/app/knowledge/wrong-answers/page.tsx`：
  - 新增 import：`documentService`, `resourceParseService`
  - 新增 `parseFailures` state
  - 新增 useEffect（Layer 3）：nodes 為空時查 `documentService.list()` 過濾 FAILED 文件 → 逐個呼叫 `resourceParseService.getStatus()` 取 failure_reason
  - 空態 UI 條件渲染：有 FAILED → 紅色警告塊（最多 3 個失敗原因 + 引導至學習庫）；無 FAILED → 原「尚無熱力圖資料」提示

**驗證**：TypeScript 編譯零錯誤

---

## ToDoList 更新

所有 4 個待辦事項已標記為 `[x]` 完成，最後更新時間戳已更新。
待辦清單目前 **零未完成項目**。

---

## 變更檔案清單

```
modified: docs/ToDoList.md                                    # 4 items → [x] done
modified: frontend/app/exam/results/page.tsx                  # 信心度四象限 UI
modified: frontend/lib/api/services.ts                        # getConfidenceAnalysis
modified: frontend/app/knowledge/wrong-answers/page.tsx       # Layer 3 空態
modified: project/features/09-學習記憶排程.feature              # 排程頁 3 Scenarios
modified: project/features/18-題目分類與考試趨勢分析.feature     # @frontend → @backend
created:  docs/todo-processing-2026-05-05T04-06-36.md         # 本紀錄檔
```
