# TiTi 董事會報告中心

> **用途**：集中管理所有排程報告與待決議事項，供董事會一站式審查。
> **更新頻率**：由排程自動產出 + CEO 統整

---

## 資料夾結構

```
reports/
  ├── README.md                  ← 本文件（報告中心索引）
  ├── pending-decisions/         ← 待董事會決議的事項
  ├── crawl-reports/             ← 每週五 02:00 考古題爬取報告
  ├── conversion-reports/        ← 每日 03:00 PDF 轉換狀態報告
  ├── doc-review-reports/        ← 每月第一週一 文件審查報告
  └── weekly-summary/            ← 每週一 CEO 週報匯總
```

---

## 報告產出排程

| 報告類型 | 產出頻率 | 排程 ID | 產出位置 |
|----------|----------|---------|----------|
| 考古題爬取報告 | 每週五 02:00 | `weekly-exam-crawl` | `crawl-reports/` |
| PDF 轉換狀態報告 | 每日 03:00 | `exam-bank-pdf-check` | `conversion-reports/` |
| 文件審查報告 | 每月第一週一 09:00 | `monthly-doc-review` | `doc-review-reports/` |
| CEO 週報 | 每週一 09:00 | 心跳機制 | `weekly-summary/` |
| 待決議事項 | 隨時（排程觸發） | — | `pending-decisions/` |

---

## 待決議事項流程

```
排程執行 → 發現需要董事會決策的事項
              │
              ▼
    寫入 pending-decisions/
    檔名：{YYYY-MM-DD}_{類型}_{主題}.md
              │
              ▼
    董事會審查 → 批准 / 否決 / 修改
              │
              ▼
    CEO 標記為已處理（移至對應報告資料夾或刪除）
```

### 待決議事項格式

```markdown
---
type: decision-request
priority: high | medium | low
from: {角色名稱}
date: YYYY-MM-DD
status: pending | approved | rejected | modified
okr: O{N}-KR{M}
---

## 決議請求：{標題}

### 背景
{為什麼需要決議}

### 選項
- **方案 A**：{描述} — 成本/風險/效益
- **方案 B**：{描述} — 成本/風險/效益

### 建議
CEO 建議：{方案 X}，原因：{...}

### 董事會決議
> （待填寫）
```

---

## 報告命名規則

| 類型 | 格式 | 範例 |
|------|------|------|
| 爬取報告 | `crawl-report-YYYY-MM-DD.md` | `crawl-report-2026-04-04.md` |
| 轉換報告 | `conversion-status-YYYY-MM-DD.md` | `conversion-status-2026-04-03.md` |
| 文件審查 | `doc-review-YYYY-MM.md` | `doc-review-2026-04.md` |
| 週報 | `weekly-YYYY-WNN.md` | `weekly-2026-W14.md` |
| 待決議 | `{YYYY-MM-DD}_{type}_{topic}.md` | `2026-04-03_cost_batch-conversion.md` |
