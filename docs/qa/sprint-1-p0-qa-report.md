# Sprint 1 P0 QA 三層驗收報告

**驗收時間**：2026-05-08 15:36（local timezone +08:00）
**驗收 branch**：`qa/sprint-1-p0-integration`（10 個 P0 commits 整合）
**驗收人**：QA 架構師 + CTO

---

## 結論：✅ 通過，可申請 CEO 簽核並上雲

| 閘門 | 狀態 | 摘要 |
|------|------|------|
| 靜態檢查 | ✅ | tsc 0 錯誤、step import lint OK、feature 37 tag 規範 |
| Pre-push gate | ✅ | F35 + F36 全綠（4 rules / 11 scenarios / 77 steps） |
| QA Layer 1 內容相關性 | ✅ | DB schema / retrieval_prompt / 互動 log / 章節對應全部對得起來 |
| QA Layer 2 UI 實測 | ✅ | 5 處互動點全綠（揭曉 / 自評 / 答對 / 答錯 / 預設摺疊） |
| QA Layer 3 空態區分 | ✅ | 合理空（200/[]）vs 不合理空（404/422）正確區分 |

---

## 閘門 #1：靜態檢查

```
Frontend tsc          0 error
Step import lint      OK — all `from .X import` targets exist
Feature tag lint      Feature 37 (新增) 0 violation
                      Feature 18, 22 (baseline pre-existing) 不影響本 PR
```

## 閘門 #2：Pre-push BDD Gate

```
behave tests/features/35-科目硬刪除.feature tests/features/36-資源硬刪除.feature
2 features passed, 0 failed, 0 skipped
4 rules passed, 0 failed, 0 skipped
11 scenarios passed, 0 failed, 0 skipped
77 steps passed, 0 failed, 0 skipped
```

---

## 閘門 #3：QA 三層驗收

### Layer 1 — 內容相關性對照表

| 子任務 | 輸入 | 輸出 | 對應 |
|--------|------|------|------|
| **T02 schema** | migration 082 upgrade | `resource_scaffolds.retrieval_prompt` (text, nullable)<br>`resource_scaffolds.template_code` (varchar(32), nullable)<br>`scaffold_interaction_log` 表（6 rows） | ✅ |
| **T04 寫入** | _build_scaffold_row(s with retrieval_prompt) | DB row 含 retrieval_prompt + template_code="K-06-study" | ✅ |
| **T08 互動 log** | 端對端點擊「我想完了」「完全想到」 | 4 viewed + 1 revealed + 1 recall_self_rated/full | ✅ |
| **T09 章節對應** | scaffold "3.1 人工智慧概念" page_start=15 page_end=25 | 2 個 approved candidates in [15,25]<br>2 questions linked to resource | ✅ |

### Layer 2 — Chrome Preview UI 實測

| 場景 | 實測 | 結果 |
|------|------|------|
| 章節閱讀路由載入 | TOC 13 章節 / article 13 H2H3 / 三欄布局 | ✅ |
| RetrievalCard 預設摺疊 | `aria-label="檢索觸發卡 — 想想看"` 存在<br>`aria-label="已揭曉重點"` 不存在 | ✅ |
| 答案不在 DOM | `body.innerText.includes('AI 可依功能分為...')` = false（揭曉前）| ✅ |
| 點「我想完了」揭曉 | `aria-label="已揭曉重點"` 出現 / 答案內容顯示 | ✅ |
| 點「完全想到」自評 | 「✓ 已紀錄」確認訊息 | ✅ |
| InlinePractice 渲染 | `aria-label="章節練習"` / 8 選項按鈕（2 題 × 4） | ✅ |
| 答對顯示「✓ 答對了！」 | 點「狹義 AI」（正解 A）後出現確認 | ✅ |
| 答錯顯示「正確答案」 | 點「歸納/演繹/類比」（錯選 B）後出現提示 | ✅ |

### Layer 3 — 空態區分

| 空態類型 | 場景 | 後端回應 | 判定 |
|----------|------|---------|------|
| **合理空** | 章節無 page range | `200 { page_range:[], questions:[] }` | ✅ 前端正確隱藏區塊 |
| **不合理空（schema 錯）** | recall_self_rated 缺 quality | `422 "requires recall_quality"` | ✅ 不允許 silent 200 |
| **合理空（資源不存在）** | scaffold_id 不存在 | `404 "scaffold not found"` | ✅ |
| **解析失敗態** | parse_status=failed + md=空 | 前端顯示「❌ 原文解析失敗：{reason}」 | ✅（T01 已驗證） |
| **解析中態** | parse_status=queued/parsing + md=空 | 前端顯示「⏳ multimodal Pro 解析中」 | ✅（T01 已驗證） |

---

## 紀錄與限制

### 已驗證
- 10 個 P0 任務在 `qa/sprint-1-p0-integration` 整合 branch 上連動運作
- 端對端互動寫入 DB 即時可見
- 教學設計：retrieval-first（揭曉前不洩答）+ testing effect（章節讀完即測）

### 當前 worktree 環境限制
- Chrome Preview screenshot 工具於本次 session 異常輸出空白，但 DOM 斷言（5 處）已替代視覺驗證
- 雲端 QA（Layer 4 雲端複測）尚未執行，待 push 後 deploy 驗證

### 雲端複測時必跑（Pre-Board Gate）
1. 登入 son731202@gmail.com 雲端帳號
2. 上傳新 PDF → 觀察 parse_status 從 queued → parsing → success 的 UX
3. 進章節閱讀頁 → 點「我想完了」→ 自評 → 觀察 DB 互動 log
4. 進有題的章節 → InlinePractice 答題 → 確認 page-range 對齊

---

## 教育顧問會稿事項（可下次 sprint 處理）

1. retrieval_prompt 寫作品質：目前注入測試時用 generic 模板「想想看 — 「{標題}」的核心要點是什麼？」過於空泛；雲端 K-06 v3 prompt 重跑後要由教育顧問抽樣 10 條真實 LLM 產出評分。
2. 自評後排程：目前只寫 log，尚未接 SM-2 排程演算法（P3 範圍）。
3. PRO 守門：T08 / T09 endpoint 沒有 `_require_paid_plan` 守門，FREE 用戶也能用 — 與 CEO Q5 決議「pitfall 全方案」一致，但需確認 RetrievalCard 是否同樣全方案開放。

---

## 簽核

- [x] CTO：3 道閘門全綠，技術交付通過
- [x] QA 架構師：三層驗收通過（Layer 1/2/3 全綠）
- [ ] 教育顧問：待會稿 retrieval_prompt 真實 LLM 產出品質
- [ ] CEO：待簽核啟動雲端 deploy

可進入 Pre-Board Gate（提交董事會前 15 項自檢）+ push 上 GitHub。
