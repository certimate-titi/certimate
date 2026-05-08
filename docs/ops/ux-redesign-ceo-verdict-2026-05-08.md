# UX/Scaffold Redesign — CEO 交付驗收 2026-05-08

> **回溯**：2026-04 由「前端工程師 + 教育顧問 + 設計師」三方做的 UX/Scaffold redesign 計畫（[ux-redesign-plan.md](docs/ux-redesign-plan.md) + [scaffold-redesign-plan.md](docs/scaffold-redesign-plan.md)），CEO 拍板 7 個決策、教育顧問定 6 個學習科學手法、4 個 Sprint 落地。本文驗收實際達成。

## 1. CEO 7 個決策題達成度

| # | 決策 | 三方建議 | 實際交付 | 評估 |
|---|------|---------|---------|:----:|
| **Q1** | `/dashboard` 改名 `/`（學習首頁） | 是 | 軟性 banner 引導 + Navbar 加 /today（T48 / Sprint 6）；hard redirect 故意延後等數據 | ⚠️ 部分達成（並存） |
| **Q2** | 答錯題強制進複習清單 | 強制 | SM-2 spaced repetition 完整（T44+T45 Sprint 5）+ `/today/reviews` 列表（T53 Sprint 7） | ⚠️ 機制完備，「強制」UX 需驗 |
| **Q3** | 圖譜降為工具入口 | 是 | `/today` 把知識圖譜放成 chip 風格（非主導航首位）；但 `/knowledge` 路由本身保留 | ⚠️ 部分達成 |
| **Q4** | 影片強制每 3-5 分暫停 retrieval | ✅ 不做（CEO 拍板簡化） | 改側欄時間戳重點：[VideoTimestampJump.tsx](frontend/components/VideoTimestampJump.tsx)（T55 Sprint 7）| ✅ 完全達成 |
| **Q5** | 概念中心優先級 | 維持 P3 | Sprint 4 T39 + Sprint 5 T49 已上線（`/library/[stub]/concept` + Voyage rerank） | ✅ 提前完成 |
| **Q6** | 動效升級 Motion 12 | 不動 | 未升級 | ✅ 達成 |
| **Q7** | 章節閱讀字體升 text-base | 升級 | 透過 `prose prose-slate` 達成（Tailwind prose 預設 16px = text-base） | ✅ 達成 |

**總計：4 完全達成 / 3 部分達成 / 0 未做**

## 2. 教育顧問 6 個學習科學手法達成度

| # | 手法 | 元件 / 實作 | Sprint | 狀態 |
|---|------|-------------|:------:|:----:|
| E1 | Karpicke retrieval-first（檢索優先 vs 灌輸） | [RetrievalCard.tsx](frontend/components/RetrievalCard.tsx) — 摺疊→揭曉→自評 | 1 | ✅ |
| E2 | Roediger testing effect（章節讀完帶題） | [InlinePractice.tsx](frontend/components/InlinePractice.tsx) | 1 | ✅ |
| E3 | Misconception correction（迷思警示） | [PitfallAlert.tsx](frontend/components/PitfallAlert.tsx) — rose 警示卡 + migration 083 | 2 | ✅ |
| E4 | Ausubel subsumption（讀前定錨） | [AdvanceOrganizer.tsx](frontend/components/AdvanceOrganizer.tsx) — violet 錨點卡 + migration 084 | 3 | ✅ |
| E5 | Bjork interleaving（跨章節交錯） | K-06 prompt v6/v7 加 interleaving 提示（T34 / T41） | 3-4 | ✅ |
| E6 | SM-2 spaced repetition | [sm2_service.py](backend/app/services/sm2_service.py) + scaffold_review_schedule + `/today/reviews` | 5-7 | ✅ |

**全部 6 個手法落地**（教育顧問簽核線索：commit `cfa5f6d`、`bb61341`、`a98aa2f`、`7359cdc`）

## 3. K-06 Prompt 模板矩陣（檔案類型分流）

原計畫 7 個檔案類型 × 1 個共用模板 = 7 個 prompts：

| 檔案類型 | template_id | 實際存在 | Sprint |
|---------|------------|:-------:|:------:|
| PDF / Markdown 學習指引 | `K-06` (study) | ✅ v3+ | 0 |
| 考古題試題卷 | `K-06-quiz` | ✅ | 1-2 |
| YouTube / MP4 影片 | `K-06-video` | ✅ | 2 |
| PPT 簡報 | `K-06-slides` | ✅ | 2-3 |
| DOCX / Markdown 筆記 | `K-06-notes` | ✅ | 3 |
| MP3 音訊 | `K-06-audio` | ✅ | 3 |
| 圖片（PNG/JPG） | `K-06-image` | ✅ | 3 |

**7/7 全部交付**（部署後 GCS 同步 17 個 prompt — 8 個 K-06 變體 + 其他）。

## 4. 跨資源學習迴圈 P3（差異化核心）

| 功能 | 實作 | 狀態 |
|------|------|:----:|
| C1 跨資源連結（mention） | scaffold_review_schedule + scaffold embedding（T54）| ✅ |
| C2 概念中心 `/library/[stub]/concept` | Sprint 4 T39 / Sprint 5 T49（Voyage rerank）| ✅ |
| C3 跨資源 retrieval prompt | retrieval_service + rerank | ✅ |
| C4 SM-2 排程整合 | T44/T45/T53 全套 | ✅ |

**4/4 P3 全部交付**（Sprint 5-7 完成，比計畫表略後 1 sprint）。

## 5. 上線後雲端實況（成本側）

從 `/admin/cost/summary`（2026-05-08 14:33 拉取）：

| 項目 | 本月用量 | 觸發/告警 |
|------|--------:|:---------:|
| Voyage（embedding + rerank）| $0.05 | 0.09% / $50 上限 |
| Gemini（parse + 抽取）| $0.01 | 0% / $100 上限 |
| Anthropic（chat）| $0 | 0% / $700 上限 |
| GCP infra | $18.98 | 4.74% / $400 上限 |

**意義**：六個學習科學手法 + 7 個檔案類型 prompt 全上線，但用戶量還太小，LLM 開銷幾乎為 0。**功能蓋好了，行銷拉用戶才是下一階段瓶頸**。

## 6. CEO 評估結論

### ✅ 達成的部分

1. **學習科學手法 100% 落地**（E1-E6 全部有對應元件與 DB schema）
2. **檔案類型分流 100% 完整**（7 個 K-06 變體 prompt）
3. **CEO 7 決策中 4 完全達成、3 部分達成、0 未做**
4. **計畫表 P0-P3 全部 ship**（Sprint 1-7 完成，含 Sprint 8 加碼的 embedding 持久化、限流訂閱層級、admin 工具）

### ⚠️ 待補的部分

1. **Q1 hard redirect 沒做** — `/dashboard` 仍是登入後預設，`/today` 靠 banner 引導
   - 風險：用戶習慣 `/dashboard` 不會主動切去 `/today`，redesign 的「3 件事聚焦」價值打折
   - 建議：等 PostHog 埋點（議題 C）兩週後看 `/today` 訪問率，決定是否硬切
2. **Q2「強制」性不夠** — SM-2 due 鷹架要用戶主動進 `/today/reviews` 才看到
   - 風險：被動 UX，留存依賴用戶自律（與 Q4 影片簡化決策一致，但複習場景強度需求不同）
   - 建議：補議題 E（Email retention 觸發）— due reminder + streak 即將斷氣 → 主動拉用戶
3. **Q3 圖譜降級不徹底** — `/today` 內降了，但 Navbar 全站還是 5 等位入口
   - 建議：Navbar 改 4 等位（學習 / 庫 / 練習 / 設定），把圖譜收進「庫 → 知識圖譜」二級選單

### 🚨 真正的問題（非 redesign 落地問題）

[功能花費佔比拆解報告](docs/finance/cost-breakdown-by-feature-2026-05-08.md) 揭露的結構性問題：

| Plan | 預估 LLM 月成本 | 售價 NTD | 預估毛利率 |
|------|---------------:|--------:|----------:|
| FREE | $0.55 | 0 | (廣告補貼) |
| PRO_199 | $3.54 | 199 | **+43%** ✅ |
| PRO_PLUS_399 | $16.30 | 399 | **-31%** 🚨 |
| ULTRA worst-case | $45 | 1,599 | (需 fair-use cap) |

**redesign 把 PRO_PLUS 限定的 `ai_coach_chat` 做太強**（advanced 模型 + 200 chat/day 配額）→ 實際每筆訂閱平均虧損。

### 推薦董事會行動點（按急迫排序）

1. **本週**：批准 ULTRA fair-use cap 落地（議題 B2 — chat 400/天、upload 500/月、token 1.5M 軟提醒、3M hard stop）
2. **兩週內**：拉 14 天 `/admin/cost/by-feature` 真實數據，驗證 `ai_coach_chat` 是否真的吃 PRO_PLUS 49%
3. **一個月內**：依數據決定 PRO_PLUS_399 三選一：(a) 漲價 NTD 599 (b) 砍 chat 200→100/天 (c) 換 cheaper model（Gemini Flash 取代 Sonnet）
4. **同步進行**（不阻擋上述）：議題 D 法務草案律師覆核 + 議題 C PostHog 埋點 ship + 議題 E Email retention

## 7. 本次評估的「不發散」結論

**Redesign 本身：完成度 95%+，三方共識的 6 個學習科學手法、7 個檔案類型分流、CEO 7 決策 4+3 全交付**。

**真正的下個瓶頸不是「還有什麼 UX 沒做」，而是「PRO_PLUS_399 結構性虧損 + 用戶量不足以驗證 redesign 的 ROI」**。

> CTO 線階段性完工。CEO 線該推的不是更多 UX 變動，而是：價值定價（B1+B2）+ 量化埋點（C）+ retention 觸發（E）三件事。
