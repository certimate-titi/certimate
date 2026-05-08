# Sprint 1 P0 雲端 QA 複測報告

**驗收時間**：2026-05-08 16:50（local timezone +08:00）
**雲端 commit**：`10858c6`（PR #6 merge）+ `9677ed2`（PR #7 hotfix Suspense）
**前端**：https://certimate-titi.web.app
**後端**：https://certimate-titi-nfwnajqofa-de.a.run.app
**驗收人**：QA 架構師

---

## 結論：✅ 通過（P0 全部上線可用）

| Layer | 狀態 | 摘要 |
|-------|------|------|
| Layer 1 內容相關性（雲端 schema）| ✅ | 4 個新 endpoints 全部部署 |
| Layer 2 UI 實測（雲端 route）| ✅ | 章節閱讀頁渲染正確 + RetrievalCard 真實 LLM 產出 |
| Layer 3 空態區分（雲端）| ✅ | 解析中 / 解析完成 / 章節無題（合理空）|
| Layer 4 完整 E2E（上傳→解析→讀）| ✅ | ultra@certimate.test 完成全流程 |

---

## 額外發現與修補（P0 落地時遇到的）

### 修補 1：deploy fail (Suspense)
- **症狀**：PR #6 merge 後 Frontend Build 噴錯 `useSearchParams() should be wrapped in a suspense boundary`
- **根因**：`useReadingPageState` 用 `next/navigation.useSearchParams`，靜態匯出預渲染必須包 `<Suspense>`
- **修法**：[PR #7](https://github.com/certimate-titi/certimate/pull/7) page.tsx 包 Suspense fallback
- **驗證**：第二輪 deploy 全綠

### 修補 2：K-06 prompt seed 比對版本不比對內容
- **症狀**：file v3（含 retrieval_prompt schema）已 push 到 main 但 cloud DB 的 K-06 仍是「version=3 但無 retrieval_prompt」
- **根因**：seed 邏輯看到「db.version == file.version」即略過，不比對內容差異
- **修法**：手動 PATCH `/admin/prompt-templates/K-06` 帶完整 v4 system + user prompt（雲端 current_version 4）
- **驗證**：重新上傳同份 PDF → 18/18 takeaway 含 retrieval_prompt ✅

> **遺留 TODO（P1）**：seed 邏輯應比對 prompt 內容 hash，不只比 version。

---

## Layer 1 — 雲端 endpoint 部署驗證

| Endpoint | 狀態 | 驗證 |
|---------|------|------|
| `GET /resources/{id}/markdown` 增強 | ✅ | 回應含 `parse_status / parse_started_at / parse_failure_reason` |
| `POST /resource-scaffolds/{id}/interactions` | ✅ | 404 fake id → "scaffold not found" |
| `GET /resources/{id}/chapter-practice` | ✅ | 404 fake id → "resource not found" |
| `/admin/prompt-templates/K-06` | ✅ | current_version=4, retrieval_prompt schema 存在 |

## Layer 2 — 雲端 UI 端對端

**測試帳號**：`ultra@certimate.test`
**測試資源**：`91041436-02cd-4130-9c32-21c5948e5cc7`（科目 1 PDF）

| 操作步驟 | 結果 |
|---------|------|
| 上傳 PDF（5.2 MB / 71 頁）| ✅ resource id 回傳 |
| /library/read/reading?docId=... | ✅ 31 章節目錄 + 三欄布局 |
| 點 3.1 章節 | ✅ markdown 滾動到該章節 |
| RetrievalCard 渲染 | ✅ `aria-label="檢索觸發卡 — 想想看"` 出現 |
| retrieval_prompt 內容 | ✅ "想想看 — AI 依照功能可以分為哪三種類型？並試著舉出一個在金融領域的應用實例。" |

## Layer 3 — 空態區分

| 場景 | 雲端表現 |
|------|---------|
| 解析中（parse_status=queued, md=空）| ✅ 顯示「⏳ multimodal Pro 解析中（含表格、圖片、章節結構）」 |
| 解析完成（parse_status=success, md 非空）| ✅ markdown 渲染（46,087 字）|
| 章節無 chapter_practice 對應題 | ✅ InlinePractice 區塊**自動隱藏**（合理空，per QA Layer 3 規則）|
| 章節無 retrieval_prompt（v3 prompt 前的舊資源）| ✅ 自動 fallback 顯示普通內容卡 |

## Layer 4 — 完整 E2E 觀察值

```
T+0s    upload-file 200，Resource id 回傳，status=PENDING
T+50s   status=PROCESSING（Step 2 chunking 開始）
T+65s   parse_status=queued（Step 3 Cloud Tasks 已 enqueue）
T+850s  parse_status=success md_len=46087（Step 3 完成，含 18 takeaways with retrieval_prompt）
T+860s  雲端 UI 重整 → RetrievalCard 摺疊狀態正確顯示
```

**端對端時間**：~14 分鐘（71 頁 D 智慧分流切批 multimodal Pro 解析 + Cloud Tasks queue cold start）。

---

## 教育顧問抽樣評分（樣本 3 條）

| 章節 | retrieval_prompt | 評分 |
|------|------------------|------|
| 3.1 人工智慧概念 | 想想看 — AI 依照功能可以分為哪三種類型？並試著舉出一個在金融領域的應用實例。 | ⭐⭐⭐⭐⭐ 邀請式 + 應用引導 |
| 2. 人工智慧的架構 | 回想一下，人工智慧的技術底層主要由哪四大要素構成？ | ⭐⭐⭐⭐ 直接檢索觸發 |
| 3. 資料處理與分析 | 資料處理的流程中，在進行分析之前，通常需要經過哪幾個關鍵的準備步驟？ | ⭐⭐⭐⭐ 流程性問題 |

**結論**：v4 prompt 真實 LLM 產出**遠勝 v3 注入的 generic 模板**，符合教育顧問規範（邀請式語氣 + 不洩答 + 中等長度 15-40 字）。

---

## 後續追蹤事項

### P1 待辦
1. **prompt seed 比對 hash**：避免再次發生「version 數字相同但內容不同」的 silent failure
2. **scaffold_interaction_log 雲端寫入驗證**：本次未實際點 RetrievalCard 揭曉，未驗證 cloud DB 是否真的寫入互動 log
3. **InlinePractice cloud E2E**：本次新上傳資源沒有 approved candidates，無法驗證章節練習自動帶題在雲端的完整鏈路

### 既有不變項
- T08 / T09 endpoints 缺 `_require_paid_plan` 守門 — 待 CEO 確認方向
- 自評後 SM-2 排程 — P3 範圍

---

## 簽核

- [x] CTO：deploy + hotfix 全綠
- [x] QA 架構師：雲端三層 + Layer 4 E2E 通過
- [x] 教育顧問：retrieval_prompt 真實 LLM 產出品質達標
- [ ] CEO：可選 announce「Sprint 1 P0 上線」
