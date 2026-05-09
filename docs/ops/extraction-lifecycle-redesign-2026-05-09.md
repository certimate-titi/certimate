# 重新分析 Lifecycle 重新設計
> 教育顧問 × CTO 聯合會議結論 — 2026-05-09

## 1. 問題 — 兩個面向同一根因

### 1.1 按鈕失效（即時 UX bug）
用戶在 `/knowledge` 點某節點 → 點「重新分析」按鈕 → 跑 unified extraction → 節點全砍重建 → 但**前端 `selectedNodeDetail` 還握著舊 `node_id`**：
- 點「練習」→ `router.push('/practice?nodeId=<deleted_id>')` → 後端 404 / 空畫面
- 點「測驗」→ 同上
- 點「定錨」鷹架 tab → `ScaffoldMaterial` 用舊 nodeId 查 N:M → 0 命中

### 1.2 進度遺失（深層架構問題）
`_clear_old_nodes` ([unified_knowledge_extraction_service.py:704](backend/app/services/unified_knowledge_extraction_service.py:704)) 是「全砍重建」：
1. 備份 mastery（user_id + node_name + base_mastery + ease_factor + ...）
2. **DELETE knowledge_nodes WHERE subject_id**（連帶 cascade 清 node_mastery / question_stats / merge_conflicts）
3. 建新節點（新 UUID）
4. `_restore_mastery_backup` 用 **name 嚴格比對** 還原 mastery

**脆弱點**：LLM 重新生成可能微調節點命名（「AI 應用場景」→「AI 商業價值與應用場景」）→ 名稱對不上 → **mastery 永久遺失**。

學生 7 天前 mastered 的節點，分析後變「未測」— 這是平台對學生的「**信任破壞**」。

## 2. 教育顧問核心原則

1. **學生 mastery 是不可逆財產** — 平台 reanalysis 是工具行為，不該毀損
2. **新增資源應該是「累積」而非「取代」** — 用戶心智模型是「我加了新教材」，不該觸發整樹重建
3. **找不到對應的 mastery 應保留 orphan**，UI 提示手動 mapping，**不該默默丟失**
4. **誤導 > 缺漏原則延伸** — 寧可顯示「未對應 mastery（X 個）需確認」，也不要錯把 60% mastery 套到不相干節點

## 3. 三層解法（按工程成本由淺入深）

### Layer 1 — 止血（本週可上線）

#### 1.1 前端：重新分析後 invalidate 前端狀態
```ts
// /knowledge/page.tsx
async function handleReExtract(subjectId: string) {
  const res = await knowledgeService.extractKnowledgeTree(subjectId);
  // 重新分析完成後：
  setSelectedNodeDetail(null);   // 清空舊 node 引用
  setSelectedDocId(null);
  setActiveNodeTab('info');
  await loadNodes(subjectId);    // 拉新樹
  showToast(`✅ 重新分析完成，新建 ${res.nodes_created} 個節點`);
}
```

#### 1.2 後端：mastery migration 升級為 embedding 對應
取代純 name 比對：
```python
def _restore_mastery_backup(self, sid: uuid.UUID):
    if not self._mastery_backup:
        return

    # 取新節點 (id, name, embedding)
    new_nodes = self.db.execute(text("""
        SELECT id, name, embedding FROM knowledge_nodes
        WHERE subject_id = :sid AND embedding IS NOT NULL
    """), {"sid": sid}).fetchall()

    orphans = []  # 找不到對應的 mastery

    for backup in self._mastery_backup:
        # 1. 嚴格 name 比對（最高信心）
        match = next((n for n in new_nodes if n.name == backup["node_name"]), None)
        method = "exact_name"

        if not match:
            # 2. embedding 比對（fallback）— 用舊節點 name 算 query embedding
            match = self._find_node_by_embedding(
                new_nodes, backup["node_name"], threshold=0.7
            )
            method = "embedding"

        if match:
            # 遷移 mastery（保留所有欄位）
            self._upsert_mastery(match.id, backup, method=method)
        else:
            # 找不到對應 → orphan
            orphans.append(backup)

    if orphans:
        # 寫入 admin 提醒（NodeMasteryOrphan 表）
        self._save_orphans(sid, orphans)
        log.warning("[mastery 遷移] %d 筆無法自動對應，需手動 mapping", len(orphans))
```

#### 1.3 UI：給用戶「重新分析」按鈕加警告
```tsx
<button onClick={() => {
  if (!confirm(
    `重新分析會重新整理知識樹結構。\n\n` +
    `現有 ${nodeCount} 個節點將：\n` +
    `• 名稱 / 結構不變的節點 → mastery 自動保留\n` +
    `• 結構改變的節點 → 嘗試用語意相似度遷移\n` +
    `• 完全找不到對應的 → 標記為「待人工確認」\n\n` +
    `確定繼續嗎？`
  )) return;
  // ... 實際觸發
}}>重新分析</button>
```

### Layer 2 — 中期：拆「新增資源」與「重新分析」兩種操作

**問題**：用戶上傳新資源 ≠ 想重新分析整樹。但目前 UI 「上傳 → 自動觸發解析（含節點關聯）」混雜兩種意圖。

**新設計**：
```
[ 上傳新資源 ]  →  resource_parse 跑（鷹架抽取 + scaffold_node_links 對既有節點計算）
                   ✅ 節點不動、mastery 不動、新鷹架自動連接
                   ⚠️ 若新資源有「全新概念」未被既有節點涵蓋，UI 提示「需要重新分析」

[ 重新分析 ]    →  unified extraction 重跑（diff merge — 見 Layer 3）
                   保守觸發：用戶**主動**選擇，伴隨上述警告
```

### Layer 3 — 長期：full 砍重建 → smart diff merge

把 `_clear_old_nodes` + `_save_knowledge_tree` 改成 diff/merge 三段式：

```
Phase A: 比對（用 embedding cosine）
  舊節點 × 新節點 N×M 配對：
  - cosine > 0.85: SAME  → 保留 ID（節點不刪不建）
  - 0.6-0.85:    UPDATE → 更新 name/desc 但 ID 不變
  - 新側無對應:    INSERT → 新增節點
  - 舊側無對應:    DELETE → 自然 cascade 清 mastery

Phase B: 套用
  - SAME/UPDATE 不動 mastery（ID 沒變）
  - INSERT 新節點 mastery=null（待學生答題建立）
  - DELETE 節點 → mastery cascade 清，但記入 orphan_mastery_log（admin 可追溯）

Phase C: scaffold_node_links 增量更新
  - SAME/UPDATE：既有 link 保留
  - INSERT：對全 subject scaffolds 跑 _link_scaffolds_to_nodes
  - DELETE：cascade 清

優點：
- 用戶無感重新分析（mastery 完全不動）
- voyage 配額省（不全 re-link）
- 學生信任不破壞
```

## 4. 工程拆解

| Task | 內容 | 工時 | 階段 |
|------|------|-----|------|
| **T93** | 前端 `/knowledge` extract 完成後 invalidate selectedNodeDetail + reload nodes | 0.5 d | Layer 1 |
| **T94** | 重新分析按鈕加 confirm 警告 dialog | 0.5 d | Layer 1 |
| **T95** | `_restore_mastery_backup` 升級 embedding 比對 + orphan 收集 | 1 d | Layer 1 |
| **T96** | `node_mastery_orphans` 表 + admin 端點 GET /admin/knowledge/orphan-masteries | 1 d | Layer 1 |
| **T97** | UI 區分「上傳資源」（不重新分析）vs「重新分析」（diff merge） | 1.5 d | Layer 2 |
| **T98** | unified extraction `--mode=incremental` 純新增節點不砍舊 | 1 d | Layer 2 |
| **T99** | `_clear_old_nodes` 改 `_diff_and_merge_nodes` smart merge | 3 d | Layer 3 |
| **T100** | BDD feature 48 — 重新分析 mastery 保留契約 | 0.5 d | Layer 1+3 |
| **總計** | | **9 d** | |

## 5. 教育顧問驗收 KPI

兩週後檢核：

| 指標 | 目標 | 量測 |
|------|------|------|
| 重新分析後 mastery 保留率 | ≥ 95% | `(SUM(restored_mastery) / SUM(backup_mastery))` |
| Orphan mastery 比率 | ≤ 5% | 找不到對應的 backup |
| 用戶「mastery 突然歸零」客訴 | 0 件 | 客服紀錄 |
| 重新分析後按鈕 404 | 0 件 | Cloud Logging filter |

## 6. 不做的事

❌ 不刪除「重新分析」按鈕（用戶有合理需求 — 例如資源大幅變更）
❌ 不直接讓重新分析 disable mastery backup（教育鐵律：學生信任）
❌ 不全自動觸發重新分析（避免上傳新資源時誤觸）

## 7. 立即可動工

按優先級：

1. **T93 前端 invalidate**（半天 — 立刻修按鈕失效）
2. **T94 confirm 警告**（半天 — 立刻警示用戶風險）
3. **T95 mastery embedding 比對**（一天 — 修進度遺失主因）
4. **T96 admin orphan 端點**（一天 — 客服協助 mapping）

T97-T99 屬 Sprint 11 範圍，等 Layer 1 觀察兩週後再啟動。

---
**Owner**：CTO（實作）+ 教育顧問（mastery KPI 驗收）+ 客戶成功（orphan 客服流程）
**回顧**：2026-05-23（兩週後拉真實數據）
