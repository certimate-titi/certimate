---
type: decision-request
priority: high
from: 後端研發 + 考題設計人員
date: 2026-04-03
status: approved
okr: O2-KR1, O3-KR1
---

## 決議請求：訂閱用戶上傳 PDF 全自動轉換 Pipeline

### 背景

董事會指示：「訂閱用戶上傳資料時不應該還需要人工批准」。需要建立 Pipeline B（用戶上傳即時轉換），與 Pipeline A（題庫批次維運）分離。

### 架構設計

```
Pipeline B — 用戶上傳（全自動）

用戶上傳 PDF
    │
    ▼ Stage 0: 內容偵測（Gemini Flash, ~1秒, $0.001）
    │
    ├── type=exam → 考題轉換 Prompt
    │      │
    │      ▼ Stage 1: PDF → MD → JSON（Gemini Flash, ~40秒, $0.005）
    │      │
    │      ▼ Layer 1-4: 4 層品質驗證（~5秒, $0.003）
    │      │
    │      ▼ 自動匯入 DB
    │
    ├── type=textbook → 知識萃取 Prompt（未來功能）
    │
    └── type=notes → 摘要生成 Prompt（未來功能）
```

### 成本控制

| 方案等級 | 每月上傳上限 | 最大月成本/用戶 |
|----------|-------------|----------------|
| FREE | 3 份 | $0.027 |
| PRO_199 | 20 份 | $0.18 |
| PRO_PLUS_399 | 50 份 | $0.45 |
| ULTRA_1599 | 無限 | 由用量監控 |

### 需要實作的項目

1. **後端 API**：`POST /api/v1/resources/upload` 增加自動觸發轉換邏輯
2. **非同步處理**：上傳後返回 202，背景執行轉換，完成後 WebSocket 通知
3. **Feature 檔**：需新增/修改 Feature 02（資源上傳）加入自動轉換場景

### 選項

- **方案 A：Phase 1 最小可行**：僅處理 `type=exam` 的 PDF，同步轉換（用戶等待 ~45 秒）。不需 WebSocket。
- **方案 B：完整異步架構**：所有類型支援，背景轉換 + WebSocket 通知 + 進度條。需要更多開發時間。

### CEO 建議

建議方案 A 先行。理由：
1. 首發市場是證照考試，`type=exam` 佔用戶上傳 80%+
2. 45 秒等待配合 loading 動畫可接受
3. 避免過度工程化，後續再迭代異步架構

### 相關 Feature 異動（🔒 GF Gate）

需修改 `project/features/02-資源上傳.feature`，新增場景：
- 「當訂閱用戶上傳考試 PDF 時，系統自動轉換為結構化題目」
- 「當系統偵測上傳內容非考題時，標記為一般資源」

### 董事會決議

> 2026-04-03 董事會批准方案 B
