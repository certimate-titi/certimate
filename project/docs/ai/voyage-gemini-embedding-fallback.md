# Voyage ↔ Gemini Embedding 備援相容性評估報告

**文件編號**: AI-cost-monitor-fallback
**產出角色**: AI/ML 工程師（CTO 技術線）
**產出日期**: 2026-04-14
**狀態**: Draft v1（技術評估，待實測驗證）
**對應 Feature File**: `project/features/33-成本監控中心.feature`
**對應 PRD**: `TECH-cost-monitor-prd`

---

## 1. 背景

Feature 33 要求在 Voyage AI 預算達到 80% 時自動降級，切換至備援 embedding provider（建議 Gemini `text-embedding-004`）以避免硬性停用心智圖生成。本文件評估兩者的相容性與切換可行性。

## 2. 兩者規格比較

| 項目 | Voyage `voyage-3` | Google Gemini `text-embedding-004` |
|------|-------------------|------------------------------------|
| 向量維度 | **1024** | **768** |
| 最大輸入 token | 32,000 | 2,048 |
| 語言支援 | 多語（中/英優化） | 多語 |
| 定價 | $0.12 / MTok | $0.025 / MTok |
| 任務類型參數 | `input_type=document / query` | `task_type=RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY` 等 |
| 距離度量 | cosine 最佳 | cosine 最佳 |
| Normalization | 內建 L2 normalized | 需手動 normalize |
| API 穩定性 | 單一 provider 風險 | Google 基礎設施穩定 |

## 3. 核心相容性問題

### 3.1 🔴 維度不一致（關鍵阻塞）
- CertiMate 現有向量欄位（推測位於 `resource_chunks.embedding`）為 **1024 維**（配合 Voyage）
- Gemini 只能輸出 **768 維**，**無法直接寫入同一欄位**
- PostgreSQL `vector(1024)` 與 `vector(768)` 是不同型別，HNSW 索引也是基於固定維度建立

### 3.2 🔴 向量空間不可混合
- 即使維度相同，**不同 embedding 模型的向量空間完全不同**
- 用 Voyage 建立的向量庫，無法用 Gemini 向量查詢（相似度計算無意義）
- 這是 embedding 模型的本質特性，不是技術選擇問題

### 3.3 ⚠️ 輸入 token 上限差異 15 倍
- Voyage 支援 32K token，單次可處理長文件
- Gemini 只有 2K token，長文件必須預先切割成更多 chunks
- 若 CertiMate 既有的 chunking 策略是 Voyage 尺寸，切到 Gemini 後需要**重新 chunking**

### 3.4 ✅ 距離度量與語言支援
- 兩者都用 cosine，演算法面無問題
- 兩者都支援繁體中文，對證照考試內容品質差異不大

## 4. 三種降級策略評估

### 策略 A：即時切換 Gemini 作為查詢 provider（不可行）
```
新查詢 → Gemini embed → 與既有 Voyage 向量庫做相似度
```
- ❌ 向量空間不同，結果無意義
- **結論：技術上不可行**

### 策略 B：切換後重建整個向量庫（成本過高）
```
達 80% → 停用 Voyage → 用 Gemini 重新 embed 所有既有 chunks → 重建 HNSW 索引
```
- 需重新處理 500+ 資源、數十萬 chunks
- 重建期間心智圖查詢全數失效（時間可能達數小時）
- 重建本身會消耗大量 Gemini 配額，可能也觸發 Gemini 門檻
- ❌ **不推薦**，降級成本遠大於受益

### 策略 C：雙軌並存（建議方案）
```
既有向量庫：保留 Voyage 1024 維不動（既有資源的查詢照常走 Voyage）
新上傳資源：切換到 Gemini 768 維，寫入新的 vector(768) 欄位
查詢時：依資源 embedding_provider 欄位分流
```
- ✅ 不需重建既有向量庫
- ✅ 達 80% 後 Voyage 只處理既有查詢（查詢本身消耗極小）
- ✅ Gemini 處理所有新資源，成本可控
- ⚠️ 需 schema 變更：`resource_chunks` 新增 `embedding_768 vector(768)` 欄位與 `embedding_provider` 欄位
- ⚠️ 查詢邏輯需依 provider 分流

### 策略 D：單純暫停新資源處理（最保守）
```
達 80% → 新上傳資源進入 pending queue，不立即 embed
通知使用者：AI 資源處理暫時延遲，待預算恢復或 Super Admin 手動擴充
```
- ✅ 零 schema 變更
- ✅ 零 provider 切換風險
- ❌ 使用者體驗受損（需等待）
- ⚠️ 需 UI 提示「處理排隊中」

## 5. 建議決策

### 🎯 首選：策略 D（暫停新資源處理）
**理由**：
1. **零技術風險**：不動既有向量庫、不新增 schema、不跨 provider
2. **符合預算護欄精神**：80% 就是警示，告訴使用者「該擴充預算或減少使用了」
3. **成本管控明確**：Voyage 用量會在 24 小時內穩定下來（沒有新資源 embed）
4. **實作簡單**：只需在資源上傳 service 加一個配額檢查

### 次選：策略 C（雙軌並存）
- 若未來 CertiMate 用量規模真的長期超過 Voyage 預算
- 應在那時再評估遷移，而非在 Feature 33 這次就做進去
- 屬於**架構演進路線圖**，不屬於本次 Feature 33 範圍

### ❌ 不採用：策略 A、B
- A 技術不可行
- B 代價遠大於效益

## 6. 對 Feature File 33 的影響

### 需修改的 Scenario
```
Example: 配額不足拒絕呼叫
  Given 當月 Voyage 累計用量為 149.90 USD
  And 本次 embedding 預估成本為 0.50 USD
  When 系統呼叫 voyage_quota_service.check_and_reserve
  Then 操作失敗
  And 錯誤代碼為 "VOYAGE_QUOTA_EXCEEDED"
- And 系統應自動切換至備援 embedding provider
+ And 系統應將該資源標記為 "pending_budget_recovery"
+ And 使用者應收到通知「AI 資源處理已排隊，因本月 embedding 預算已達上限」
```

### 需新增的 Scenario
```
Example: 達 80% 門檻後新資源進入等待佇列
  Given 當月 Voyage 累計用量達到 40 USD（80% 門檻）
  When 使用者 "user@certimate.com" 上傳新資源
  Then 操作成功
  And 資源狀態應為 "pending_budget_recovery"
  And 系統應建立站內通知告知使用者「AI 處理已排隊」

Example: Super Admin 擴充預算後佇列恢復處理
  Given 有 3 筆資源狀態為 "pending_budget_recovery"
  When 使用者 "super@certimate.com" 將 AI_VOYAGE 月預算擴充至 100 USD
  Then 操作成功
  And 3 筆等待中的資源應重新進入處理佇列
```

## 7. 結論給 CTO

1. **Voyage → Gemini 即時切換在技術上不可行**（向量空間不相容）
2. 建議降級動作改為 **「暫停新資源處理並排隊」**（策略 D）
3. 對 Feature File 33 需做 2 處調整（一刪一加，詳見第 6 節）
4. 雙軌向量庫（策略 C）列入未來架構演進路線圖，非本次範圍
5. 此決策需回饋給 CEO / 產品經理，因為會輕微影響 UX 描述

---

**待 CTO Review 決定：**
- [ ] 同意改為策略 D？
- [ ] 是否需回 CEO 確認 UX 訊息措辭？
- [ ] 是否要在本次加上「pending 佇列恢復處理」的背景任務？
