# 產品決策紀錄：L1 節點鷹架整合（知識頁右側面板 UI 簡化）

日期：2026-05-09
Sprint：9
Commit：416f647（branch: fix/knowledge-node-scaffold-merge）
Feature Spec：`project/features/03b-知識心智圖導航.feature` — Rule「節點驅動鷹架呈現」

---

## 改動前後對照（用戶可見變化）

| 面向 | 改動前 | 改動後 |
|------|--------|--------|
| 「資訊」tab | 顯示 mastery badge + citation badge + sourceText 大段原文摘錄 | 顯示 mastery badge + citation badge + 「此節點的學習鷹架」區塊（ScaffoldMaterial） |
| 「鷹架教材」tab | 顯示依 nodeId 篩選的 ScaffoldMaterial（takeaway / elaborative） | 顯示空提示：「學習鷹架已整合至『資訊』頁籤，請切換查看」 |
| sourceText 原文 | 佔據「資訊」tab 下半部，數百字原文展示 | 完全移除，不再渲染 |
| ScaffoldMaterial 位置 | 獨立 tab 才可見 | 點擊節點即在「資訊」tab 立即可見，降低操作步數 |
| tab 數量 | 4（資訊 / 鷹架教材 / 筆記 / AI 教練） | 4（結構不變，避免破壞 component 介面） |

---

## 教育顧問建議（全文）

教育顧問於 2026-05-08 評估知識頁右側面板後給出以下意見：

「目前『資訊』tab 同時展示 sourceText 大段原文與 mastery / citation meta，
而『鷹架教材』tab 展示的 takeaway 鷹架本質上已是原文的精煉結構化版本。
兩者並陳會讓學習者視線在冗長原文與精煉鷹架間分裂，
符合 Sweller（1988）split-attention effect 的典型反面案例，
認知負荷白白消耗在格式切換，而非深度處理。

建議：移除 sourceText 顯示，將 ScaffoldMaterial 前移至『資訊』tab 節點點擊即見，
讓錨點（節點）→ 鷹架（takeaway/elaborative）的 Ausubel subsumption 路徑最短化。
『鷹架教材』tab 暫保留空提示，維持介面穩定性，等 L2 升級後再決定是否拆除。」

---

## 學理依據

| 原則 | 對應決策 |
|------|---------|
| Sweller split-attention（1988） | 移除 sourceText，消除原文與鷹架並陳的認知分裂 |
| Ausubel subsumption（1960） | ScaffoldMaterial 緊貼節點錨點展示，擴展路徑最短 |
| Karpicke testing > re-reading（2011） | 砍除重讀內容（sourceText），學習行為導向答題與鷹架消化 |
| Bjork desirable difficulty（1994） | mastery 繼續由 SM-2 答題決定，不靠原文重讀提升熟悉度 |

---

## 廢棄的 UX 設計

1. **sourceText 顯示**：資訊 tab 下半部的大段原文摘錄，完全移除。未來若需要原文溯源，由 citation badge 連結跳轉資源，不在右側面板行內展示。
2. **雙 tab 並陳（鷹架教材 / 資訊各有一套內容）**：原設計讓用戶需切換 tab 才能看到鷹架，現整合為點擊節點即見，「鷹架教材」tab 退化為引導提示。

---

## 待觀察 KPI（兩週內，截止 2026-05-23）

| 指標 | 觀察方式 | 目標 |
|------|---------|------|
| 鷹架展開次數 | PostHog event `scaffold_section_viewed` | 較整合前週均值 +20% |
| 鷹架答題完成率 | 鷹架 elaborative 題目完成 / 展示比 | > 40% |
| 「鷹架教材」tab 點擊率 | PostHog event `tab_click{tab: scaffold}` | < 5%（確認用戶已轉向「資訊」tab） |
| 用戶回饋 | in-app 拇指評分（知識頁節點面板） | 負面回饋 < 3 件 / 週 |

若「鷹架展開次數」兩週後未達目標，優先排查 fallback 機制是否正確觸發（節點無鷹架 → resource 層鷹架）。

---

## 後續可選改動

### a. 拆掉「鷹架教材」tab（4 tab → 3 tab）

- 時機：兩週 KPI 確認用戶不再使用「鷹架教材」tab（點擊率 < 2%）後
- 風險：破壞現有 component prop interface，需 CTO 評估 breaking change 範圍
- 需更新：`03b-知識心智圖導航.feature` 對應 Scenario + 前端 RightPanel component

### b. L2 鷹架對應升級（voyage embedding）

- 目標：以 voyage embedding 計算 node ↔ scaffold 語意相似度，取代目前純靠 `chapter_heading` 字串比對
- 效益：跨節點鷹架推薦更精準，fallback 品質提升
- 需評估：embedding 計算成本（每次節點點擊 vs. 預先 batch index）
- 前置：ERM DBML 新增 `scaffold_node_embeddings` 表，CTO 簽核後排 Sprint 10+
