# language: zh-TW
@feature_47 @node_scaffold_links @sprint_10 @backend
Feature: 節點 ↔ 鷹架關聯（解決對不起來架構斷層）
  覆蓋 Sprint 10 T80-T86：
  - T80 migration 090 scaffold_node_links N:M + knowledge_nodes.embedding
  - T81 unified extraction 寫節點 embedding
  - T82 parse pipeline 算 cosine 寫 link
  - T85 get_node_scaffolds 走 N:M 表
  - T86 前端不再 fallback resource 全集

  完整 spec 見 docs/ops/node-scaffold-pipeline-redesign-2026-05-09.md。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And alice 訂閱科目「AI 應用規劃師」，已執行 unified extraction（5 個 chapter 節點）

  @backend
  Rule: 節點 embedding 在 unified extraction 時自動寫入
    Scenario: extraction 後所有節點 embedding 不為 NULL
      Given alice 觸發 POST /reverse-engineering/subjects/{sid}/extract
      Then knowledge_nodes 含 embedding 的 row 比例 = 100%
      And embedding 為 1024 維 vector

    Scenario: voyage 失敗時節點仍寫入但 embedding 為 NULL
      Given voyage API 暫不可用
      When extraction 執行
      Then 節點 row 仍 commit（業務不阻斷）
      And embedding 為 NULL，後續可由 admin backfill 補

  @backend
  Rule: parse pipeline 寫 scaffold_node_links（embedding 對應）
    Scenario: 上傳新資源 → 鷹架自動關聯到節點
      Given alice 有 5 個 chapter 節點 + embedding
      When alice 上傳 PDF，parse 完成
      Then scaffold_node_links 含若干 row
      And 每筆 link 的 similarity > 0.55
      And 同 (scaffold_id, node_id) 不重複（UNIQUE 約束）

    Scenario: similarity 低於門檻不寫 link（誤導 > 缺漏）
      Given 該 PDF 有 scaffold「YouTube 影片時間戳」與所有節點都不相似
      When parse pipeline 跑
      Then 該 scaffold 在 scaffold_node_links 0 個 link

  @backend
  Rule: get_node_scaffolds 走 N:M 表（取代舊 page/chapter 比對）
    Scenario: 點節點回對應鷹架（按 similarity 排序）
      Given node_X 有 5 條 scaffold_node_links similarity 0.9 / 0.8 / 0.75 / 0.7 / 0.6
      When alice GET /knowledge-map/nodes/{node_X}/scaffolds
      Then 回 200，scaffolds 5 個，按 similarity DESC 排序
      And 每筆含 similarity 欄位

    Scenario: 節點無對應 link → 誠實回空陣列
      Given node_Y 無任何 scaffold_node_links
      When alice GET /knowledge-map/nodes/{node_Y}/scaffolds
      Then 回 200，scaffolds = []
      And 前端顯示「此節點尚無對應鷹架」（不再 fallback resource 全集）

    Scenario: FREE 用戶仍 paywall
      Given bob 為 FREE
      When bob GET /knowledge-map/nodes/{any}/scaffolds
      Then 回 403，paywall = true

  @backend
  Rule: unified extraction 重跑 → scaffold relink
    Scenario: 重跑 extraction 後既有 scaffold 重新關聯
      Given alice 已有 100 筆 scaffold_node_links
      When alice 重新觸發 extraction（節點重新生成）
      Then 舊 scaffold_node_links 全部刪除
      And 新節點建好後 _relink_subject_scaffolds 跑 → 新 link 寫入
      And scaffolds.embedding 不變（節省 voyage 配額）

  @backend
  Rule: 節點刪除時 link 自動 cascade
    Scenario: 刪節點 → 對應 link 一併消失
      Given node_Z 有 3 筆 link
      When node_Z 被刪除
      Then scaffold_node_links 中 node_id=node_Z 的 row = 0
