# ToDoList 自動巡檢紀錄

**時間**：2026-04-30 20:05 (自動排程巡檢)
**執行者**：TiTi Commander 自動巡檢
**類型**：定期待辦事項狀態檢查

---

## 巡檢摘要

對 `docs/ToDoList.md` 中所有未完成項目（`- [ ]`）進行逐一驗證，共檢查 14 項，結果如下：

| 狀態 | 數量 |
|------|------|
| ✅ 已解決（本次標記完成） | 5 |
| 🔴 仍未解決 | 9 |

---

## ✅ 本次確認已解決的項目（5 項）

### 1. `/dashboard` — 備考模式標籤 Sprint/Standard/Mastery
- **原狀態**：無任何 Feature 覆蓋（首見：2026-04-24）
- **現狀態**：Feature 13 Rule (L379-411) 已新增三個 Example Scenario 分別覆蓋 Sprint、Standard、Mastery 模式，前端 `page.tsx` (L363-365) 亦已實作三模式 UI
- **結論**：Feature + 實作皆完整，標記完成

### 2. `/exam/results` — 成績卡片下載按鈕無 Feature Scenario
- **原狀態**：功能為 stub，無 Feature 覆蓋（首見：2026-04-24）
- **現狀態**：Feature 06 (L143-148) 已新增 Rule「下載成績卡片按鈕應顯示為 placeholder 未實作狀態」含 Example Scenario
- **結論**：Feature 已覆蓋（功能本身為 placeholder 但 spec 已明確定義行為），標記完成

### 3. `/super-admin/platform-subjects` — 平台科目管理無 Feature 覆蓋
- **原狀態**：無任何 Feature 覆蓋（首見：2026-04-27）
- **現狀態**：Feature 12c Rule「平台科目管理頁應支援列表/編輯/啟停用」(L271-282) 已新增，Feature 34 亦覆蓋相關 Fork API
- **結論**：Feature 覆蓋完整，標記完成

### 4. `/resources/[id]/candidates` — 前端頁面尚未建立
- **原狀態**：`frontend/app/resources/[id]/candidates/page.tsx` 不存在（首見：2026-04-27）
- **現狀態**：頁面檔案已建立
- **結論**：前端頁面已存在，標記完成

### 5. `/review` — KaTeX/MathContent 渲染待確認
- **原狀態**：MathContent component 是否實際執行 KaTeX 渲染待確認（首見：2026-04-28）
- **現狀態**：`frontend/components/MathContent.tsx` 確認 import `rehype-katex`、`remark-math`、`katex/dist/katex.min.css`，透過 `<ReactMarkdown>` 搭配 `remarkPlugins={[remarkMath]}` 和 `rehypePlugins={[rehypeKatex]}` 完整實作 KaTeX 渲染
- **結論**：功能實作完整，標記完成（Feature 07 仍無對應 Scenario，但歸類為「可選補強」非阻塞）

---

## 🔴 仍未解決的項目（9 項）

### 🔴 Feature 缺失類（3 項）

| # | 路由 | 問題 | 首見 |
|---|------|------|------|
| 1 | `/dashboard` | StudyBuddyBanner（ULTRA 共讀橫幅）無任何 Feature 覆蓋 | 2026-04-27 |
| 2 | `/exam/workspace` | Feature 05 AI 打氣語句（Certi mascot）無對應 UI 實作 | 2026-04-29 |
| 3 | `/pricing` | PRO_PLUS_399「進階 AI 教練」標記 `false`，與 Feature 03 / Feature 18 規格衝突 | 2026-04-30 |

### 🟠 實作缺失類（3 項）

| # | 路由 | 問題 | 首見 |
|---|------|------|------|
| 4 | `/super-admin/anomaly` | Feature 16「批次修復」情境缺乏對應 UI（無 checkbox 多選 + 批次按鈕） | 2026-04-24 |
| 5 | `/knowledge` | 「+ 新增資源」按鈕導向 `/dashboard` 而非上傳 modal | 2026-04-28 |
| 6 | `/exam/workspace` | Feature 05 Certi 打氣介面無任何 UI 元素（重複列於 Feature 缺失） | 2026-04-29 |

### 🟡 空態補強類（4 項，皆違反 Layer 3 規則）

| # | 路由 | 問題 | 首見 |
|---|------|------|------|
| 7 | `/practice` | no-questions 空態未實際查詢 `resource_parse_jobs` 取 failure_reason | 2026-04-24 |
| 8 | `/review` | `wrongQuestions.length === 0` 未查 job 表，無法區分真正全答對 vs job FAILED | 2026-04-28 |
| 9 | `/schedule` | `recs.length === 0` 未查 schedule job 表 | 2026-04-29 |
| 10 | `/account/weekly-reports` | `reports.length === 0` 未查週報產生 job | 2026-04-30 |

### 其他（1 項）

| # | 項目 | 問題 |
|---|------|------|
| 11 | GCP Billing Export | Cloud Run 環境變數 + Service Account key 待部署 |

---

## 建議優先處理順序

1. **P0** `/pricing` PRO_PLUS_399 AI 教練標記錯誤 — 影響用戶升級決策，修復僅需改一行 `included: true`
2. **P1** Layer 3 空態補強（4 項） — 違反 QA 驗收規則，但需後端配合新增 API
3. **P1** `/super-admin/anomaly` 批次修復 UI — Feature 16 已定義，實作缺失
4. **P2** `/exam/workspace` Certi 打氣 — 新功能，需設計 + 實作
5. **P2** `/dashboard` StudyBuddyBanner Feature — 僅需補 Feature Scenario
6. **P3** `/knowledge` 新增資源按鈕導向 — UX 改善

---

## 變更紀錄

- 更新 `docs/ToDoList.md`：5 項標記為已完成（`[x]`），附確認說明與時間戳
- 建立本紀錄檔 `docs/todo-processing-2026-04-30T20-05-23.md`
