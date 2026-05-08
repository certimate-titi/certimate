# language: zh-TW
@feature_45 @rate_limit_tier @scaffold_backfill @sprint_8 @backend
Feature: JWT plan claim 接訂閱層級限流 + scaffold embedding 補齊（後端契約）
  覆蓋 Sprint 8：
  - T58 _generate_token 加 plan claim → RateLimitMiddleware 真的識別 PRO/ULTRA 層級
  - T57 backfill_scaffold_embeddings 腳本 + T66 admin endpoint 觸發
  - T60 dashboard 上傳後輪詢 parse-status 取 failure_reason

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And 已存在 ULTRA 用戶 "ultra@example.com"
    And 已存在 SUPER_ADMIN 用戶 "admin@certimate.com"

  @backend
  Rule: JWT plan claim 帶入正確訂閱層級
    Scenario: PRO 用戶登入後 token 含 plan="PRO"
      When alice POST /auth/login
      Then 回 200，access_token decode 後 payload.plan = "PRO"

    Scenario: ULTRA 用戶 refresh token 仍帶 plan
      Given ultra 已持有有效 token
      When ultra POST /auth/refresh
      Then 回 200，新 token payload.plan = "ULTRA"

    Scenario: PRO 用戶 QPS 上限 60（Sprint 7 smoke fix 後設定）
      Given alice 在 1 秒內並發 65 次 GET /resources
      Then 至少 5 次回 429

    Scenario: ULTRA 用戶 QPS 上限 200
      Given ultra 在 1 秒內並發 250 次 GET /resources
      Then 至少 50 次回 429

  @backend
  Rule: scaffold embedding backfill admin endpoint
    Scenario: SUPER_ADMIN 觸發 backfill，背景 task 排入
      Given DB 有 100 筆 resource_scaffolds.embedding IS NULL
      When admin POST /admin/backfill-scaffold-embeddings?limit=50
      Then 回 200，{"queued": true, "null_count": 100, "limit": 50}

    Scenario: 無 NULL 時不啟動背景 task
      Given DB 全部 scaffold 已有 embedding
      When admin POST /admin/backfill-scaffold-embeddings
      Then 回 200，{"queued": false, "null_count": 0}

    Scenario: 非 SUPER_ADMIN 無權限
      When alice POST /admin/backfill-scaffold-embeddings
      Then 回 403，message = "需要 SUPER_ADMIN 權限"

  @backend
  Rule: dashboard 上傳後輪詢 parse-status（T60 對應契約）
    Scenario: parse 成功 → 回應結構含終態
      Given alice 上傳 PDF，背景 parse 完成
      When alice GET /resources/{resource_id}/parse-status
      Then 回 200，status = "COMPLETED"

    Scenario: parse 失敗 → failure_reason 可讀
      Given alice 上傳壞掉的 PDF，後端 parse job 標 FAILED 並寫入 failure_reason
      When alice GET /resources/{resource_id}/parse-status
      Then 回 200，status = "FAILED"，failure_reason 不為 NULL
