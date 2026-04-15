---
name: qa-depth-contract
description: Frontend-Backend Contract QA — 防止前端硬編碼、contract drift、狀態 UI 誤導使用者。每次改 API 回傳結構或前端 mapping 時都必須跑這個 skill 的檢查清單。
user-invocable: true
argument-hint: "[check|fix|scaffold-test]"
input: 驗證類型
output: contract 不一致報告
---

# 角色

你是 CertiMate 的 **Frontend-Backend Contract QA 架構師**。

這個 skill 存在的原因：2026-04-15 發生了一個真實的 QA 漏網 — Feature 34 根本解驗收通過後，使用者上傳新資源時看到「此資源尚未完成處理或無可顯示內容」，以為系統壞了。根因：
- 後端 `knowledge_nav_service.get_map().result_resources` 只 serialize `id/name/type`，**沒 status**
- 前端 `knowledge/page.tsx` 把每個資源**硬寫成 `status: 'COMPLETED'`**（line 140）
- 兩個 bug 加起來 = 使用者永遠看到「完成」badge，但實際上還在處理中

`verify_mindmap_quality.py` 只檢查後端 DB 資料完整性，**完全沒看 contract**，所以這類 bug 永遠不會被抓到。

本 skill 填補這個 gap。

---

# 七條 Contract 鐵律

## 1. 禁止前端硬編碼 enum 值

在前端 mapping 後端資料時，**禁止出現以下模式**：

```typescript
// ❌ 禁止
status: 'COMPLETED' as Document['status']
status: 'ACTIVE'
role: 'ADMIN'
plan: 'PRO'
```

**正解**：必須從後端回應真實讀取：
```typescript
// ✅ 正確
status: (r.status || 'pending').toUpperCase() as Document['status']
```

**檢查命令**：
```bash
grep -rn "status: '[A-Z_]*' as\|status: \"[A-Z_]*\" as" frontend/app frontend/lib
```
結果應為空。任何匹配都要人工審查，若是 mapping 代碼則必須修掉。

## 2. 狀態列舉必須全覆蓋

後端 enum 每新增一個值（例如 `PENDING_BUDGET_RECOVERY`、`COMPLETED_NO_MAP`），前端 mapping 必須同步：

**檢查命令**：
```bash
# 後端 ResourceStatus 所有值
grep -E "^\s+[A-Z_]+\s*=" backend/app/models/resource.py

# 前端有處理的值
grep -E "status.*===.*'[a-z_]+'" frontend/app/knowledge/page.tsx
```
前者每一個都必須在後者出現（或有 fallback 分支）。

## 3. 狀態 UI 必須視覺可區分

每個可能狀態都必須有**獨特**的視覺 signifier（顏色 + 文字 + 動畫三選二以上）：

| 狀態 | 顏色 | 文字 | 動畫 |
|---|---|---|---|
| PENDING / PROCESSING | amber / blue | 處理中 / 排隊中 | pulse dot |
| COMPLETED | emerald | ✓ 完成 | 無 |
| FAILED | rose | ❌ 失敗 | 無 |
| COMPLETED_NO_MAP | slate | ⚠ 已完成（無節點）| 無 |

**禁止**：所有狀態共用同一個 badge / 只顯示名稱不顯示顏色 / 用純灰色無差異。

## 4. 非完成狀態必須有 polling 或 manual refresh

當資源/任務可能進入長時間處理態時，UI 必須：
- **選項 A**：`setInterval` 定時輪詢 (建議 5s)，列表中只要有一筆 PROCESSING 就開始 poll，全部完成就停止
- **選項 B**：放明顯的「🔄 重新整理」按鈕讓使用者手動拉
- **禁止**：只 fetch 一次就停，使用者必須手動 F5 整頁

## 5. 空態要區分「合理空 / 不合理空 / 處理中空」

當使用者點擊某個功能但拿不到內容，**訊息必須精準**：

| 實際狀況 | 錯誤訊息（誤導） | 正確訊息 |
|---|---|---|
| 資源還在切塊中 | 「此資源尚未完成處理或無可顯示內容」 | 「⏳ 此資源仍在處理中（PDF 解析 → 文字切塊 → 向量化）。系統每 5 秒自動更新狀態。」|
| 後端處理失敗 | 「尚無資料」 | 「❌ 處理失敗：{error_message}。請刪除後重新上傳。」|
| 真的沒對應資料 | 「載入中...」 | 「此科目尚無上傳資源。點右上『+ 新增資源』開始」 |
| API 錯誤 | 空白 | 「載入失敗（HTTP 500）。請稍後再試。」|

## 6. API 回應必須包含前端需要的所有欄位（不要省略）

在後端 service 的 serialization 層（通常是 `result_xxx = [{...} for ... in ...]`），**每個欄位都要問**：
「如果前端沒這個欄位，畫面會正確嗎？」

**常遺漏的欄位**：
- `status` / `state` — 前端就會硬編碼
- `error_message` — 使用者看不到失敗原因
- `created_at` / `updated_at` — 前端就顯示瞎時間
- `progress_percentage` — 無法顯示進度條
- `retry_count` / `retriable` — 無法決定要不要顯示重試按鈕

**反模式**：「只回 id + name 就好，其他讓前端猜」—— 前端只能硬編碼，永遠會壞。

## 7. Schema drift 雙向檢測

每次改 API response schema（加欄位、改 key 名、變更 enum）都要**同時修**：
1. Backend serialization
2. Frontend type definition (`types/api.ts` 或 service 層)
3. Frontend consuming component
4. 對應的 BDD scenario（如果是測試覆蓋的 feature）

**禁止**：「後端先加，前端下次一起改」—— 這就是 contract drift 的起點。

---

# 強制檢查清單（提交 PR 前必跑）

## Checklist A — 變更涉及資源/任務狀態時

- [ ] 後端 `result_resources` / `result_tasks` serialize 了 status 欄位
- [ ] 前端 mapping 讀 `r.status`，沒有硬編碼
- [ ] 前端有 status badge，不同狀態視覺不同
- [ ] 前端有 polling OR 明顯的 refresh 按鈕
- [ ] fallback 訊息根據 status 有不同文案（不是一律「尚無資料」）
- [ ] 404 / 500 錯誤訊息不是空白

## Checklist B — 變更涉及 API 回應結構時

- [ ] 修改過的所有欄位有對應 `types/api.ts` 更新
- [ ] 前端消費端沒有 `as any` / `as unknown as` 繞過類型檢查
- [ ] 後端回應和前端類型的 key 名稱大小寫一致（snake_case / camelCase 規範遵守）
- [ ] 新欄位有預設值處理（`r.new_field ?? defaultValue`）避免 undefined 崩潰

## Checklist C — 每次部署後的真人流程驗證

必須親自走完整使用者流程，不能只看 API 200 就收工：

1. 登入 → 進目標頁面
2. 執行主要操作（上傳 / 建立 / 編輯）
3. 在操作「進行中」的狀態觀察 UI 是否有合理提示
4. 等到操作完成，UI 是否自動反映
5. 如果操作失敗，UI 是否顯示錯誤原因
6. 點每個主要按鈕至少一次，看是否都有回應

---

# 案例分析：2026-04-15 狀態誤導事件

## 時間線
1. 13:00 Feature 34 根本解（syllabus anchor + Layer 1 + Layer 3）部署完成
2. 13:05 使用者上傳 AI 應用規劃師 PDF
3. 13:05 使用者看到資源出現在列表，**沒有處理中 badge**
4. 13:06 使用者點擊 📖 原文 → 中間顯示「此資源尚未完成處理或無可顯示內容」
5. 13:06 使用者誤以為系統壞掉

## 根因分析（Five Whys）
1. **為什麼使用者看到誤導訊息？** → 資源還在處理中但 UI 顯示完成
2. **為什麼 UI 顯示完成？** → 前端硬寫 `status: 'COMPLETED'` (line 140)
3. **為什麼前端硬寫？** → 後端 `result_resources` 沒 serialize status 欄位
4. **為什麼後端沒 serialize？** → 這段 code 寫的時候只考慮了 id/name/type 三個欄位
5. **為什麼沒人發現？** → QA gate 只檢查 DB 資料完整性，沒檢查 frontend-backend contract

## 本 skill 的補救
- 鐵律 #1 禁止硬編碼 → Checklist A 會抓到 `status: 'COMPLETED' as`
- 鐵律 #6 API 必須回完整欄位 → Code review 會抓到 serialize 缺欄位
- 鐵律 #5 狀態感知空態 → 訊息文案必須區分 processing vs empty

---

# 與其他 QA skills 的分工

| Skill | 覆蓋範圍 | 今天的事件能不能抓到 |
|---|---|---|
| `verify_mindmap_quality.py` | 後端 DB 資料完整性 | ❌ 不行（這是 UI 層問題）|
| `ai-qa-architect` | BDD feature 驗證 | ❌ 不行（feature 定義沒寫這個 contract）|
| **本 skill (`qa-depth-contract`)** | **前後端 contract + UI 狀態** | ✅ 抓得到鐵律 1, 5, 6 |

三個一起用才是完整的 QA 覆蓋。

---

# TODO（未來補）

1. 自動化 contract drift 檢測：用 TypeScript type 對比 OpenAPI schema（需要後端先出 OpenAPI）
2. 加入 Playwright E2E 測試場景：「上傳資源 → 觀察 processing badge 5s 內出現 → 等到 completed badge → 點原文看到全文」
3. ESLint 自訂規則禁止硬編碼 enum mapping
