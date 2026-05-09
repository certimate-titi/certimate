# language: zh-TW
@feature_48 @extraction_diff_merge @sprint_11 @backend
Feature: 重新分析 lifecycle — smart diff merge 取代全砍重建（mastery 保留契約）
  覆蓋 Sprint 11 T99-T100：
  - T99 _diff_and_merge_nodes 取代 _clear_old_nodes + _save_knowledge_tree
  - 既有節點 ID 保留 → mastery / scaffold_node_links / questions 不動
  - 沒對應的舊節點 → DELETE + mastery 寫入 node_mastery_orphans

  完整 spec 見 docs/ops/extraction-lifecycle-redesign-2026-05-09.md。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And alice 訂閱科目「AI 應用規劃師」，已執行過 unified extraction
    And 既有節點 N1「AI 倫理與規範」alice 答題建立 mastery=0.6（base_mastery）

  @backend
  Rule: SAME — cosine > 0.85 節點 ID 與 mastery 完全保留
    Scenario: 第二次 extraction LLM 回傳完全相同節點名稱
      Given LLM 重生成新樹仍含「AI 倫理與規範」節點
      When 觸發 unified extraction
      Then knowledge_nodes 中該節點 ID 不變
      And node_mastery 中 (alice, N1) row 不被刪除
      And base_mastery 仍為 0.6
      And scaffold_node_links 中 node_id=N1 的 row 不被刪除

  @backend
  Rule: UPDATE — cosine 0.6-0.85 微調節點仍保留 ID
    Scenario: LLM 微調節點命名
      Given LLM 把「AI 倫理與規範」改名為「AI 倫理、法規與社會影響」
      And 兩名稱 voyage cosine = 0.78
      When 觸發 unified extraction
      Then 節點 ID 仍為 N1（不變）
      And name 更新為新名稱
      And source_text 更新為新 description
      And base_mastery 仍為 0.6（mastery 保留）
      And questions.node_id = N1 的題目仍可正常作答

  @backend
  Rule: INSERT — 新節點 mastery 為空，等學生答題建立
    Scenario: LLM 引入全新節點「Generative AI 倫理」
      Given alice 上傳新資源含「Generative AI 倫理」內容
      When 觸發 unified extraction
      Then knowledge_nodes 含新節點（新 UUID）
      And node_mastery 對應 (alice, 新ID) 不存在（mastery=0）
      And 對該 subject 既有 scaffolds 算 cosine 寫入 scaffold_node_links

  @backend
  Rule: DELETE — 舊節點無對應 → 進 node_mastery_orphans
    Scenario: 舊節點「過時技術」LLM 重生成不再涵蓋
      Given alice 對舊節點 N2「Symbolic AI」有 mastery=0.4
      When LLM 新樹完全沒「Symbolic AI」相似節點（cosine 全部 < 0.6）
      Then knowledge_nodes 中 N2 row 被刪除（CASCADE 清 mastery）
      And node_mastery_orphans 含 (alice, "Symbolic AI", 0.4, "pending")
      And admin GET /admin/knowledge/orphan-masteries 可看到該筆

  @backend
  Rule: 按鈕失效防護（前端 + 後端）
    Scenario: extraction 完成後前端 invalidate selectedNodeDetail
      Given alice 點重新分析按鈕，獲得 confirm 對話框
      When alice 確認，extraction 完成
      Then 前端 selectedNodeDetail 被清空
      And nodes / mindMapNodes 重新載入
      And alice 不會看到指向已刪除節點的「練習/測驗/定錨」按鈕

    Scenario: 即使前端沒 invalidate，後端 DELETE 節點 + 自然 cascade 也不破壞 FK
      Given 舊 alice 帳號頁面仍持有已刪節點 N2 的 nodeId
      When alice 點「練習 nodeId=N2」
      Then 後端回 404 節點不存在（不是 500）
      And 前端應 fallback 到節點清單

  @backend @kpi
  Rule: KPI — mastery 保留率
    Scenario: 重新分析後 mastery 保留率 ≥ 95%
      Given alice 在 subject 有 20 個 mastery row
      And LLM 重新生成節點 95% 有對應（SAME 或 UPDATE）
      Then 重新分析後 node_mastery 至少保留 19 row（95%）
      And node_mastery_orphans 至多 1 row（5%）
