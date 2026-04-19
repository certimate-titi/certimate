# ToDoList 待辦事項處理紀錄

**處理時間**：2026-04-17T14:34:13 UTC（排程自動執行）
**處理方式**：TiTi Commander 排程巡檢

---

## 待辦事項一覽

| # | 待辦項目 | 處理狀態 | 說明 |
|---|---------|---------|------|
| 1 | RAG資料流程_修正版 vs 目前實作差異比較 | ✅ 已完成分析 | 詳見下方報告 |
| 2 | 重新整理平台管理功能 | ✅ 已完成分析 | 詳見下方報告 |
| 2a | 用戶管理 — 無法看到用戶詳情 | ⚠️ 需確認 | 前端頁面已實作，可能為 API 回應格式問題 |
| 2b | 用戶管理 — 寄信給用戶功能失效 | ❌ 前端缺失 | 用戶詳情頁缺少「發送通知」按鈕 |
| 2c | 用戶管理 — 停權後應寄信並自動切換 | ❌ 邏輯缺失 | 停權後未觸發通知，按鈕未動態切換 |
| 2d | Prompt 模板 — 無法編輯 | ✅ 已實作 | 編輯功能可用（system_prompt / user_prompt / temperature） |
| 2e | Prompt 模板 — AI 模型選擇 | ❌ 前端缺失 | 編輯表單缺少 model 下拉選單 |

---

## 一、RAG 資料流程_修正版 vs 目前實作差異比較

### 1.1 總體評估

設計文檔 `docs/RAG資料流程_修正版` 與實際後端實作的對比結果：**整體實裝完成度約 85-90%**。核心 RAG 流程（文件處理 → 向量化 → 檢索 → 知識樹萃取）已完全實裝，部分前端整合與邊界場景仍有空白。

### 1.2 功能對照表

| 設計文檔需求 | 實裝狀態 | 評分 | 涵蓋檔案 |
|-------------|---------|------|---------|
| 結構化提煉（6 大頂級章節心智圖） | ✅ 完全實現 | 10/10 | `unified_knowledge_extraction_service.py` |
| 物理級跳轉（點擊節點高亮原文） | ⚠️ 部分實現 | 6/10 | `knowledge_map.py` 有 source API，但無行號/anchor_id |
| 動態增刪（資源實時增量更新） | ✅ 完全實現 | 10/10 | `document_processing_service.py` |
| 權威優先（官方考綱 vs 輔助標記） | ✅ 完全實現 | 10/10 | `unified_knowledge_extraction_service.py` syllabus_anchor 機制 |
| Gemini Pro/Flash 分工 | ⚠️ 已改進 | 9/10 | 改用 Gemini Flash（成本優化），非設計文檔的 Pro 分工 |
| Document AI + Gemini Flash 路由 | ✅ 完全實現 | 9/10 | `document_processing_service.py` 10 級管道 |
| Voyage 向量 1024 維 | ✅ 完全實現 | 10/10 | `embedding_service.py` 非對稱嵌入 |
| 二階段檢索（pgvector + Reranker 2.5） | ✅ 完全實現 | 10/10 | `retrieval_service.py` Tier 1-B 標準 |
| Mindmap 動態填充（向量重心路由） | ✅ 完全實現 | 10/10 | `mindmap_strength_service.py` 三層計算 |
| 錨點導航（source_id + anchor_id） | ⚠️ 部分實現 | 6/10 | `resource_chunk.py` 有 metadata，無 anchor_id 欄位 |
| Mastery 引擎（僅模擬考更新） | ✅ 完全實現 | 10/10 | `unified_knowledge_extraction_service.py` restore_mastery_backup |
| 配額控制（Voyage 月度預算） | ✅ 完全實現 | 10/10 | Feature 33 完整實裝 |

### 1.3 架構亮點

1. **4 層 PDF 結構分析**：Tier 1 書籤（零成本）→ Tier 2 LLM 目錄（1 API 呼叫）→ Tier 3 正則標題（零成本）→ Tier 4 LLM 批次（fallback）
2. **配額感知閘控**（Feature 33）：嵌入前檢查 Voyage 預算，80% 時標記 PENDING_BUDGET_RECOVERY，100% 拒絕
3. **考綱錨點強制約束**（Feature 34 §3）：LLM 產出的 6 章必須 1:1 對應考綱，不得自由創造
4. **Mastery 遷移**：備份舊節點掌握度 → 新節點精確匹配 → Fallback node_mapping → 未對應節點保留
5. **三層支撑度計算**：直接 chunks ×2 + 語意 chunks ×1 + 考古題 ×1，飽和公式 min(total/10, 1.0)

### 1.4 待改進項目

| 項目 | 現況 | 建議 |
|------|------|------|
| 物理級跳轉 | knowledge_map.py 有 source API 但返回全文本，無行號 | 在 resource_chunks metadata 加入 anchor_id，API 返回 highlight_line |
| 向量快取 | 每次檢索重新計算查詢向量 | Redis 快取最近 1000 個查詢向量（TTL 24h），節省 Voyage 配額 15-20% |
| Chunk 映射算法 | 三層策略邏輯冗長（~100 行） | 抽象為 MapperStrategy 介面，策略可外掛 |
| 考古題 node_id=NULL | AI 生成時多次 subject-level fallback，邏輯分散 | 建立「科目級虛擬節點」統一映射 |

---

## 二、平台管理功能分析

### 2.1 當前架構

| 模組 | 前端路徑 | 後端路由 | 完整度 |
|------|---------|---------|--------|
| 營運儀表板 | `/super-admin/dashboard` | `/admin/dashboard` | ✅ 完整 |
| 用戶管理 | `/super-admin/users` + `[userId]` | `/admin/users` | ⚠️ 部分問題 |
| 財務與訂閱 | `/super-admin/finance` | `/admin/finance` | ✅ 完整 |
| 內容與安全 | `/super-admin/moderation` | `/admin/moderation` | ✅ 完整 |
| 系統設定 | `/super-admin/settings` | `/admin/system-settings` | ✅ 完整（但過於龐雜） |
| 審計日誌 | `/super-admin/audit-logs` | `/admin/system-settings/audit-logs` | ✅ 完整 |
| Prompt 模板 | `/super-admin/prompt-templates` + `[templateId]` | `/admin/prompt-templates` | ⚠️ 前端缺 model 選擇 |
| 成本監控 | `/super-admin/cost-monitor` | `/cost-monitor` | ✅ 完整 |

### 2.2 問題詳細分析

#### 問題 2a：用戶詳情「無法看到」

**實際情況**：前端頁面 `users/[userId]/client.tsx` 已完整實作，包含 6 個資訊區塊：
- Profile（基本資料 + 頭像 + 狀態）
- Subscription（訂閱方案 + 到期日 + 權限來源）
- Usage（上傳/考試/問答/OCR 統計卡片）
- Token（今日/月度 Token 用量 + 消耗分佈圓餅圖）
- Login History（最近 20 次登入紀錄）
- Anomalies（異常紀錄）

**可能原因**：
1. 用戶列表頁 `users/page.tsx` 的連結可能未正確導向 `users/[userId]`
2. API 回應格式 `GET /admin/users/{userId}` 的欄位可能與前端預期不符（例如：後端回傳 `behavior` 但前端讀 `usage`）
3. 需實際操作測試確認（QA 驗收）

**建議**：進行端到端測試確認頁面載入是否正常。

#### 問題 2b：寄信給用戶功能失效

**實際情況**：
- 後端 API 存在：`POST /admin/users/{userId}/notify`
- 前端用戶詳情頁 **沒有** 「發送通知」按鈕或輸入框
- 頁面只有：恢復正常、停權帳號、刪除用戶帳號、調整訂閱等級

**修復方案**：在 `users/[userId]/client.tsx` 新增通知功能：
```
需新增：
1. 「發送通知」按鈕（Mail icon）
2. Modal 包含：主旨輸入框、內容 textarea、發送按鈕
3. 呼叫 POST /admin/users/{userId}/notify API
```

#### 問題 2c：停權後應寄信並自動切換

**實際情況**：
- 停權按鈕（line 187-198）呼叫 `superAdminService.suspendUser()` 後只做 `setUserData` 更新狀態
- 未觸發 `superAdminService.notifyUser()` 發送通知信
- 「恢復正常」和「停權帳號」兩個按鈕同時顯示，未根據 status 動態切換

**修復方案**：
1. 停權成功後，自動呼叫 `POST /admin/users/{userId}/notify` 發送停權通知
2. 根據 `userData.status` 動態顯示按鈕：`active` 時顯示「停權」，`suspended` 時顯示「恢復」

#### 問題 2d：Prompt 無法編輯 — ✅ 已實作

**實際情況**：`prompt-templates/[templateId]/client.tsx` 編輯 Tab 功能完整：
- System Prompt textarea ✅
- User Prompt textarea ✅
- Temperature 數值輸入 ✅
- 變更說明 ✅
- 「儲存並遞增版本」按鈕 ✅
- 版本歷史 + 回滾 ✅
- A/B 測試建立與管理 ✅

**結論**：Prompt 編輯功能已實作，此項應標記為完成。可能的問題是用戶不知道如何進入編輯頁面（需要從列表頁點擊進入詳情頁的「編輯 Prompt」Tab）。

#### 問題 2e：Prompt AI 模型選擇

**實際情況**：
- 後端 API `PATCH /admin/prompt-templates/{templateId}` 已支援 `model` 欄位更新
- `CreateTemplateRequest` 和 `UpdateTemplateRequest` 都有 `model` 字段
- 前端 header 顯示當前模型（`模型：{template.model}`）
- **但編輯表單中沒有 model 下拉選單**
- `handleSave` 只傳送 `system_prompt`、`user_prompt`、`temperature`、`change_note`，未包含 `model`

**修復方案**：在編輯表單的 Temperature 旁新增 Model 下拉選單：
```
需新增：
1. <select> 下拉選單，選項包含 gemini-2.5-flash / claude-3.5-sonnet / gpt-4o 等
2. 新增 model state：const [model, setModel] = useState(template.model)
3. handleSave 中傳送 model 欄位
```

### 2.3 功能分類優化建議

**系統設定頁面過於龐雜**（6 個 Tab 集中一頁），建議拆分：
- **AI 配置**：AI 模型路由、方案限額 → 與成本監控合併或鄰近
- **營運管理**：公告管理 → 可獨立為 `/super-admin/announcements`
- **開發配置**：Feature Flags、版本資訊 → 保留在設定頁
- **帳號管理**：管理員帳號 → 保留在設定頁

**功能完整性確認**：
- ✅ 財務模組：MRR/ARPU/LTV/Churn Rate + 交易 + 退款 + 優惠碼 — 完整
- ✅ 內容審核：AI 濫用監控 + 檢舉佇列 + 統計 — 完整
- ✅ 審計日誌：列表 + 匯出 CSV — 完整
- ⚠️ 用戶管理：基礎完整，缺通知功能與停權自動化
- ⚠️ Prompt 模板：編輯可用，缺 model 選擇 UI

---

## 三、行動清單

| 優先級 | 項目 | 負責角色 | 類型 |
|--------|------|---------|------|
| P1 | 用戶詳情頁載入驗證（端到端測試） | QA 架構師 | 驗證 |
| P1 | 新增「發送通知」按鈕至用戶詳情頁 | 前端工程師 | 開發 |
| P1 | 停權後自動發送通知信 + 按鈕動態切換 | 前端工程師 | 開發 |
| P1 | Prompt 編輯表單新增 model 下拉選單 | 前端工程師 | 開發 |
| P2 | 物理級跳轉（anchor_id）完善 | 後端工程師 + 前端工程師 | 開發 |
| P2 | 向量快取機制（Redis） | 後端工程師 | 優化 |
| P3 | 系統設定頁面拆分重組 | 前端工程師 | 重構 |
| P3 | Chunk 映射策略抽象化 | 後端工程師 | 重構 |

---

*本紀錄由 TiTi Commander 排程巡檢自動產出*
