# language: zh-TW
@feature_44 @scaffold_embedding @rate_limit @sprint_7_p6 @backend
Feature: Scaffold embedding 持久化 + 互動 log 限流豁免（後端契約）
  覆蓋 Sprint 7 P6 T54-T55 + smoke fix：
  - T54 _embed_scaffolds 在 parse 完成後寫入 voyage 1024 維 embedding
  - /concept-center 偏好用 DB 內 embedding，避免每次 query 重 embed
  - smoke fix：scaffold interactions log 不佔用戶 QPS（reading 頁瞬間並發保護）

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @backend
  Rule: Scaffold embedding 持久化
    Scenario: parse 完成後 scaffold 自動寫 1024 維 embedding
      Given 用戶 alice 上傳 PDF 並完成 parse
      When 查詢產出的 resource_scaffolds
      Then 每筆 scaffold.embedding 為 1024 維 vector
      And embedding 不為 NULL

    Scenario: voyage embed 失敗時 scaffold 仍寫入但 embedding 為 NULL
      Given voyage API 暫時不可用
      When parse pipeline 跑 _embed_scaffolds
      Then scaffold rows 仍 commit（業務不阻斷）
      And 失敗 scaffold.embedding 為 NULL
      And log 含 "voyage embed failed, scaffold persisted without embedding"

    Scenario: /concept-center 偏好走 DB embedding
      Given 用戶 alice 有 50+ scaffolds 皆含 embedding
      When GET /concept-center?q=機器學習
      Then 命中走 DB cosine similarity，不再 call voyage embed
      And response latency < 200ms

  @backend
  Rule: scaffold interactions 限流豁免
    Scenario: reading 頁瞬間並發 12 筆 interactions log 不觸發 429
      Given 用戶 alice 為 FREE 方案（QPS=30）
      When 1 秒內並發 POST /api/v1/resource-scaffolds/{id}/interactions × 12
      Then 全部回 2xx，無 429
      And X-RateLimit-Remaining 不被該批次扣抵

    Scenario: 一般 API 仍受限流保護
      Given 用戶 alice 為 FREE 方案（QPS=30）
      When 1 秒內並發 GET /api/v1/resources × 50
      Then 至少 20 筆回 429（超過 free 30 QPS 閾值）
