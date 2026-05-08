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

  @backend @plan_tier_routing
  Rule: AI 教練對話依 plan 路由不同模型（T72 — 救 PRO_PLUS 毛利）
    Background:
      Given migration 088 已套用，ai_model_routings 表含 7 行 plan-tier routing
      And 已存在 PRO_PLUS 用戶 "pp@example.com"

    Scenario: PRO_PLUS 用戶 ai_coach_chat 走 Haiku（節省 92% token 成本）
      Given pp 對某錯題發起 AI 教練對話
      When wrong_answer_service.ai_coach_chat 呼叫 LLM
      Then 解析 (plan="PRO_PLUS", task_type="advanced") 走 primary_model = "claude-haiku-4-5"
      And ai_usage_ledger 記錄 endpoint = "claude-haiku-4-5"，cost_usd 估算用 Haiku 價格

    Scenario: ULTRA 用戶仍走 Sonnet（保留高階體驗）
      Given ultra 對某錯題發起 AI 教練對話
      When wrong_answer_service.ai_coach_chat 呼叫 LLM
      Then 解析 (plan="ULTRA", task_type="advanced") 走 primary_model = "claude-sonnet-4-5"
      And ai_usage_ledger 記錄 endpoint = "claude-sonnet-4-5"，cost_usd 估算用 Sonnet 價格

    Scenario: PRO 用戶與 PRO_PLUS 同走 Haiku
      Given alice 對某錯題發起 AI 教練對話
      When wrong_answer_service.ai_coach_chat 呼叫 LLM
      Then 解析 (plan="PRO", task_type="advanced") 走 primary_model = "claude-haiku-4-5"

    Scenario: ANTHROPIC_API_KEY 無效時 PRO_PLUS 自動 fallback 到 Gemini Flash
      Given pp 對某錯題發起 AI 教練對話
      And ANTHROPIC_API_KEY 暫時失效
      When LLMService.resolve_model("PRO_PLUS", "advanced")
      Then 改回傳 fallback_model = "gemini-2.5-flash"

    Scenario: knowledge_nav AI 教練亦遵循同 routing
      Given pp 在 /knowledge 對節點發起對話
      When knowledge_nav_service._generate_coach_reply 呼叫 LLM
      Then llm.generate(plan="PRO_PLUS", task_type="advanced") 走 Haiku
      And feature 標籤為 "ai_coach_chat"

  @backend @plan_tier_routing
  Rule: ai_model_routings UNIQUE 約束防重複行
    Scenario: 同 (plan, task_type) UPSERT 不新增重複行
      Given 已存在 (plan="ULTRA", task_type="advanced") 一筆 routing
      When migration 088 重跑（idempotent）
      Then ai_model_routings 中 (plan="ULTRA", task_type="advanced") 仍為 1 行
      And primary_model 被更新為最新值
