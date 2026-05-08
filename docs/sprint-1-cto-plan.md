# Sprint 1 CTO 開發計畫書

**Sprint 期程**：2026-05-08 → 2026-05-14（7 天）
**對應**：[scaffold-redesign-plan.md](scaffold-redesign-plan.md) P0 + [ux-redesign-plan.md](ux-redesign-plan.md) Sprint 1
**Worktree**：`/Users/simon/certimate/project/.claude/worktrees/strange-wilbur-9ac155`
**狀態追蹤**：本文件每日更新 ✅/⏳/❌

---

## 0. Sprint 1 範圍

### 必交付
1. **解析中 UX**（已本地驗證，恢復 stash）— `/markdown` API 加 parse_status，前端三分支
2. **前端基礎重構** — 抽 `useKnowledgePageState` + `useNodeScaffoldData` hook（不破現有功能）
3. **章節閱讀獨立路由** `/library/[stub]/reading`
4. **K-06 prompt 升級** — 加 `retrieval_prompt` 欄位產出規則
5. **DB schema** — `resource_scaffolds` 加 `retrieval_prompt` + `template_code` + 新表 `scaffold_interaction_log`
6. **新元件** — `RetrievalCard.tsx` + `InlinePractice.tsx`
7. **章節練習 endpoint** — `GET /resources/{id}/chapter/{heading}/practice`
8. **BDD scenarios** — RetrievalCard 互動 + 章節練習自動帶題

### 不做（順延 Sprint 2+）
- K-06-video / K-06-quiz / K-06-slides 等其他模板
- pitfall / advance_organizer 類別
- 跨資源連結
- 學習首頁 IA 重劃（dashboard → /）

---

## 1. 任務拆解（10 個 PR）

| # | 任務 | 預估 | 優先 | Branch |
|---|------|------|------|--------|
| **T01** | 恢復 stash + UX loading 三分支 PR | 1 hr | P0a | `feat/p0a-markdown-parse-status` |
| **T02** | DB migration 071：scaffold schema 升級 | 2 hr | P0b | `feat/p0b-scaffold-schema-migration` |
| **T03** | K-06 prompt 加 retrieval_prompt schema | 2 hr | P0c | `feat/p0c-k06-retrieval-prompt` |
| **T04** | 後端 _persist_parsed 寫入 retrieval_prompt | 2 hr | P0d | `feat/p0d-backend-retrieval-write` |
| **T05** | 前端重構：抽 useKnowledgePageState hook | 6 hr | P0e | `refactor/p0e-knowledge-state-hook` |
| **T06** | 前端重構：抽 useNodeScaffoldData hook | 4 hr | P0f | `refactor/p0f-scaffold-data-hook` |
| **T07** | 章節閱讀獨立路由 /library/[stub]/reading | 6 hr | P0g | `feat/p0g-reading-route` |
| **T08** | RetrievalCard 元件 + 互動 log endpoint | 5 hr | P0h | `feat/p0h-retrieval-card` |
| **T09** | InlinePractice 元件 + chapter practice endpoint | 5 hr | P0i | `feat/p0i-inline-practice` |
| **T10** | BDD scenarios + QA 三層驗收 | 4 hr | P0j | `test/p0j-bdd-scenarios` |

**總工時估算**：37 hr（單人 5 工作天，預留 2 天 buffer + QA）

---

## 2. 依賴圖（執行順序）

```
T01 (UX loading) ─┐
                   ├─ 可獨立 push
T03 (K-06 prompt) ─┤
                   │
T02 (DB migration) ───→ T04 (後端寫入) ───→ T08 (RetrievalCard)
                                          ↘
T05 (knowledge hook) ──→ T06 (scaffold hook) ──→ T07 (reading route) ──→ T08, T09
                                                                          ↓
                                                                        T10 (BDD)
```

**並行機會**：
- 第 1 天：T01 + T02 + T03 並行（互不依賴）
- 第 2 天：T04 + T05 + T06 並行（DB 已就緒）
- 第 3-4 天：T07 → T08 / T09 並行
- 第 5-6 天：T10 + 整合 QA

---

## 3. 進度追蹤表

| ID | 任務 | 狀態 | 開始 | 完成 | PR | 備註 |
|----|------|------|------|------|----|------|
| T01 | UX loading 三分支 | ⏳ | 2026-05-08 | — | — | stash 待 pop |
| T02 | DB migration 071 | ⏳ | — | — | — | — |
| T03 | K-06 prompt schema | ⏳ | — | — | — | — |
| T04 | 後端 retrieval_prompt 寫入 | ⏳ | — | — | — | 依賴 T02 + T03 |
| T05 | useKnowledgePageState hook | ⏳ | — | — | — | — |
| T06 | useNodeScaffoldData hook | ⏳ | — | — | — | — |
| T07 | /library/[stub]/reading 路由 | ⏳ | — | — | — | 依賴 T05 |
| T08 | RetrievalCard 元件 | ⏳ | — | — | — | 依賴 T04 + T07 |
| T09 | InlinePractice 元件 | ⏳ | — | — | — | 依賴 T07 |
| T10 | BDD scenarios | ⏳ | — | — | — | 全部完成後 |

**狀態圖例**：⏳ 待辦 / 🔄 進行中 / ✅ 完成 / ❌ 阻塞 / ⏸ 暫停

---

## 4. 每日 Checkpoint

### Day 1（2026-05-08）
- [ ] T01 PR open + merge（恢復已驗證的 UX loading）
- [ ] T02 migration 完成 + 本地 alembic upgrade 通過
- [ ] T03 K-06 prompt schema 草稿（教育顧問會稿）

### Day 2（2026-05-09）
- [ ] T04 後端 retrieval_prompt 寫入（含單測）
- [ ] T05 useKnowledgePageState 抽出（不改 UI 行為）
- [ ] T06 useNodeScaffoldData 抽出（不改 UI 行為）

### Day 3-4（2026-05-10/11）
- [ ] T07 章節閱讀路由（含 generateStaticParams 靜態匯出處理）
- [ ] T08 RetrievalCard 元件 + 互動 log API
- [ ] T09 InlinePractice + chapter practice endpoint

### Day 5（2026-05-12）
- [ ] T10 BDD scenarios（RetrievalCard 互動 + 章節練習自動帶題）
- [ ] QA 三層驗收（內容 / UI / 空態）

### Day 6-7（2026-05-13/14）
- [ ] 雲端部署驗證
- [ ] 整合 smoke test
- [ ] Sprint Demo + 教育顧問簽核

---

## 5. 技術決定

### 5.1 DB Migration 策略
- 加欄位用 `nullable=True`，歷史資料保留 NULL
- 新表 `scaffold_interaction_log` 全新建立
- 不 backfill 歷史資源（per CEO Q1 決議：Lazy backfill — 用戶下次點才重跑）

### 5.2 前端重構策略
- **不破現有功能**：抽 hook 不改 UI 行為，先確保現有測試 100% 綠燈再加新功能
- **漸進式拆分**：先抽 1 個 hook → 跑 TS + 測試 → 確認綠 → 再抽下一個
- **Snapshot 測試**：T05 / T06 重構前後拍 Chrome Preview 截圖比對

### 5.3 路由設計
- `/library/[stub]/reading?docId=X&chapter=Y` — 用 stub + query string（靜態匯出限制）
- Firebase rewrite 須同時設有/無尾斜線兩版（per 違規歷史）
- `useReadingPageParams()` 從 `window.location.pathname + search` regex 解析

### 5.4 RetrievalCard 行為
- 預設摺疊（per CEO Q4 決議轉化）
- 點擊「我想完了 → 看答案」展開 + 寫入 `scaffold_interaction_log`
- 揭曉後回想感選擇（沒想到 / 想到一半 / 完全想到）寫入 `node_mastery`
- HMR / 重整後保持已揭曉狀態（localStorage 紀錄）

### 5.5 InlinePractice 行為
- 章節結尾自動 fetch 該章節對應 question_candidates（按 source_page 對齊）
- 取 2-3 題（已答過的去除）
- 復用 `practiceService.startMicroPractice()`（不改既有作答 UI）

---

## 6. 風險紀錄

| 風險 | 影響 | 緩解 | 觸發條件 |
|------|------|------|----------|
| T05 重構破壞現有功能 | 高 | 漸進式 + Chrome Preview snapshot 對照 | useState 數量超過 30 個 |
| T07 靜態匯出動態路由失敗 | 高 | 用 stub + regex 模式（已有先例） | Firebase rewrite 雙版未設 |
| K-06 prompt 改動影響歷史資源 | 中 | Lazy backfill（CEO 已簽） | 用戶反映歷史資源沒 retrieval_prompt |
| 章節對齊 source_page 偏差 | 中 | 加 ±2 頁容錯 + log 紀錄不對齊案例 | T09 整合測試 |
| BDD fixture 重做工作量大 | 低 | 每個新 endpoint 只做 1 happy path + 1 error | T10 |

---

## 7. 退出條件（Sprint 1 完成判定）

- ✅ 10 個 T01-T10 全部 merge 進 main
- ✅ Frontend `tsc --noEmit` 0 錯誤
- ✅ Backend `behave --tags=~@ignore` 全綠
- ✅ Pre-Board Gate 15 項自檢全綠（per [compliance-gate.md](../.claude/skills/titi-commander/references/compliance-gate.md)）
- ✅ Cloud deploy 成功
- ✅ 雲端 QA 三層驗收通過（Layer 1 內容 / Layer 2 UI / Layer 3 空態）
- ✅ 教育顧問簽核 RetrievalCard 互動模式
- ✅ 設計師簽核 RetrievalCard / InlinePractice 視覺
- ✅ Sprint Demo 紀錄歸檔

---

## 8. CTO 每日心跳模板

```
## Sprint 1 Day {N} 心跳 - {date}

### 完成
- T0X: {brief}（PR #X）

### 進行中
- T0Y: {brief}（{progress}%）

### 阻塞
- {若無寫無）

### 明日預定
- T0Z

### 風險異動
- {若無寫無）

### Feature drift 檢查
- 已新增 / 修改 Scenario：{清單}
```

---

## 9. 下一步

**現在執行**：T01（恢復 stash + UX loading）— 已本地驗證，最快可 push。

