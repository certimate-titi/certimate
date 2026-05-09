# 知識節點 ↔ 學習鷹架 Pipeline 重新設計
> 教育顧問 × CTO 聯合會議結論 — 2026-05-09

## 1. 問題回顧

L1 整合（PR #25）後使用者反映「節點和鷹架對不起來」。診斷結果是 **架構斷層**，非 UI 缺陷：

| 元件 | 來源 | resource_id | 識別欄位 |
|------|------|:-----------:|----------|
| `knowledge_nodes` | `unified_knowledge_extraction_service` 跨資源萃取 | **NULL**（科目層）| name + Bloom levels |
| `resource_scaffolds` | `resource_parse_service` 單資源解析 | 該 PDF | chapter_heading + page |

兩條路徑各跑各的，**沒有 N:M 關聯**；現有 `get_node_scaffolds` 用「page 比對 + chapter_heading 子字串」對應，命中率極低 → 前端 fallback 拿整個 resource 全部鷹架 → **不論點哪個節點看到的都一樣**。

## 2. 教育顧問核心原則

1. **節點 = 考綱概念**（abstract pedagogical unit）；**鷹架 = 教材切片**（concrete content unit）— 兩者本質不同，不該扁平化合併
2. **品質勝於覆蓋率** — 寧可一個節點對 0 鷹架顯示空白，也不要對到無關鷹架（誤導 > 缺漏，這是學習科學鐵律）
3. **節點命名應對齊考綱**（已部分達成）；**鷹架命名應對齊節點**（缺）
4. **節點 mastery 由答題驅動，鷹架是內容呈現** — L1 的責任分離原則保留

## 3. 新 Pipeline 設計（A–F 六階段）

```
┌─────────────────────────────────────────────────────────────┐
│ Phase A: 節點生成（保留現有 — unified extraction）          │
│   考古題摘要 + chunk 摘要 + syllabus → Gemini → 兩層知識樹  │
│   depth=1 chapter / depth=2 section（resource_id=NULL）     │
│   ⊕ 新增：寫入 knowledge_nodes.embedding（從 source_text）  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase B: 鷹架生成（保留現有 — resource_parse）              │
│   PDF parse → K-06 prompt → 6 種 scaffold                  │
│   resource_scaffolds.embedding 已 T54 寫入                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase C [新增]: 節點 ↔ 鷹架自動關聯（parse 後同步跑）       │
│   ① 取該科目所有 unified node 的 embedding                  │
│   ② 對每個新 scaffold 算 cosine vs all nodes                │
│   ③ top-3 且 similarity > 0.6 → 寫入 scaffold_node_links    │
│   ④ 無命中 → 不寫（保留空關聯，UI 顯示「尚無對應」）        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase D [新增]: 節點重萃取時重建關聯                        │
│   unified extraction 重跑：                                 │
│   ① 暫存舊節點 embedding（mastery 已有 backup 機制）        │
│   ② 新節點建好後 → 觸發 Phase C 對全 subject 的 scaffolds   │
│   ③ scaffold_node_links 整批刷新                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase E [新增]: 節點合併時鷹架繼承                          │
│   knowledge_merge_service 合 A→B 時：                       │
│   UPDATE scaffold_node_links SET node_id=B WHERE node_id=A │
│   ON CONFLICT (scaffold_id, node_id) DO NOTHING            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase F [新增]: 品質閘門 + 監控                             │
│   ① 節點關聯 0 鷹架 → admin dashboard 標紅                  │
│   ② Scaffold 全 similarity<0.4 → 標 orphan                  │
│   ③ 兩週 review 命中率，調 threshold                        │
└─────────────────────────────────────────────────────────────┘
```

## 4. Schema 改動（migration 090）

```sql
-- 4.1 N:M 關聯表
CREATE TABLE scaffold_node_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scaffold_id UUID NOT NULL REFERENCES resource_scaffolds(id) ON DELETE CASCADE,
  node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  similarity FLOAT NOT NULL,  -- cosine 0–1
  link_method VARCHAR(20) NOT NULL,  -- 'embedding' / 'chapter_match' / 'manual'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(scaffold_id, node_id)
);
CREATE INDEX ix_snl_node_sim ON scaffold_node_links(node_id, similarity DESC);
CREATE INDEX ix_snl_scaffold ON scaffold_node_links(scaffold_id);

-- 4.2 節點加 embedding（已有則跳過）
ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS embedding vector(1024);
```

## 5. 教育顧問驗收 KPI（兩週後檢核）

| 指標 | 目標 | 量測方式 |
|------|------|----------|
| 每節點對應鷹架數 | 平均 3-8 | `SELECT node_id, COUNT(*) FROM scaffold_node_links GROUP BY node_id` |
| Orphan scaffold 比率 | < 10% | scaffold 無任何 link 的比率 |
| Orphan node 比率 | < 20% | depth=2 節點無 link（depth=1 chapter 抽象度高，可接受） |
| 命中 similarity 分布中位數 | > 0.65 | 確認 threshold 設定合理 |
| 用戶主觀滿意度 | 70%+ | PostHog 加「鷹架幫助度 👍/👎」按鈕 |

## 6. CTO 工作量拆解

| Task | 內容 | 工時 |
|------|------|------|
| **T80** | migration 090（scaffold_node_links + knowledge_nodes.embedding） | 0.5 day |
| **T81** | KnowledgeNode embedding backfill（重用 T57 backfill 模式） | 1 day |
| **T82** | Phase C：parse pipeline 加 `_link_scaffolds_to_nodes()` | 1.5 day |
| **T83** | Phase D：unified extraction 重跑時觸發 relink | 1 day |
| **T84** | Phase E：merge service 維護 scaffold_node_links | 0.5 day |
| **T85** | 改寫 `get_node_scaffolds` 走新 N:M 表 | 0.5 day |
| **T86** | 移除前端 `getResourceScaffolds` fallback（教育顧問鐵律：不誤導） | 0.5 day |
| **T87** | Phase F：admin dashboard 顯示 orphan 統計 | 1 day |
| **T88** | BDD feature 47 — 節點鷹架關聯契約 | 0.5 day |
| **總計** | | **~7 day（1 sprint）** |

## 7. 上線分階段（避免一次大爆炸）

### Sprint 9 P0（本週）— 緊急止血
- **T86**：前端不再 fallback resource 全集（顯示空白比顯示無關內容好）
- 用戶體感立刻改善（不再「對不起來」）
- 風險：暫時很多節點顯示無鷹架（誠實面對資料品質問題）

### Sprint 10 P1（下週）— 對應建立
- **T80 + T81 + T82**：schema + backfill + 新 parse hook
- 新上傳資源自動帶關聯，舊資源跑 backfill script

### Sprint 10 P2（下週）— 修復連動
- **T83 + T84 + T85**：unified extraction 重跑、merge、新 query 邏輯
- 此時 node_scaffolds endpoint 走新 N:M 表

### Sprint 11 P3（再下週）— 品質監控
- **T87 + T88**：admin dashboard + BDD spec
- 兩週 KPI review 後決定是否調 threshold

## 8. 不做的事（避免 scope creep）

❌ 把節點和鷹架合併成單一 entity（教育原則：本質不同，不該合）
❌ 完全捨棄 chapter_heading（仍保留作 fallback hint）
❌ 跨科目 / 跨用戶共用節點關聯（每用戶有自己的 fork）
❌ 即時動態算 cosine（每次點節點都算 → 慢 + 浪費 voyage 配額；改預先算寫入 DB）

## 9. 教育顧問簽核

- ✅ 節點 mastery 仍由答題驅動（Bjork desirable difficulty）
- ✅ 鷹架關聯走 embedding（內容相似度 = subsumption 距離）
- ✅ 品質閘門避免誤導（與 L1 原則一致）
- ✅ 6 種 scaffold 類別不變（takeaway/pitfall/elaborative/advance_organizer/strategy/concept_extract）

## 10. 下一步

- 立即動工 **T86**（半天工作量、立刻體感改善）
- 這個 redesign doc 進入 PR，CEO 簽核後排 Sprint 10 動工

---
**Owner**：CTO（實作）+ 教育顧問（驗收）+ 財務（voyage 配額成本核對）
**回顧**：2026-05-23（兩週後拉真實數據）
