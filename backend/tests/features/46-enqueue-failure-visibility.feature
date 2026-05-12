@feature_46 @enqueue_failure @issue_68 @backend
Feature: 背景排程失敗應立刻標記 resource FAILED（後端契約）
  覆蓋 Issue #68 — production YT 上傳 silent PENDING 永久卡住的修補。

  歷史：2026-05-12 雲端 UI sweep 發現 POST /resources/youtube 後 resource
  狀態 PENDING 永久不變、parse_job 從未建立。根因：enqueue_process_resource
  在 Cloud Tasks 配置缺失時 fallback inline thread，inline 失敗無觀測性。

  修補：worker 模式下 enqueue 失敗即 raise EnqueueFailedError →
  API 標記 resource FAILED + error_message + 回 503。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @backend
  Rule: WORKER_SERVICE_URL 缺失 → raise EnqueueFailedError
    Scenario: worker 模式無 WORKER_SERVICE_URL → 拋出 EnqueueFailedError
      Given 環境變數 BACKGROUND_PROCESSOR=worker
      And 環境變數 WORKER_SERVICE_URL 未設定
      When 呼叫 enqueue_process_resource(resource_id, user_id, tenant_id)
      Then 拋出 EnqueueFailedError
      And 錯誤訊息含 "WORKER_SERVICE_URL 未設定"

  @backend
  Rule: API endpoint catch EnqueueFailedError → 標記 FAILED + 503
    Scenario: submit_youtube 排程失敗即標記 resource FAILED
      Given 用戶 alice 已建立資源 "yt-test" status="PENDING"
      And 環境變數 BACKGROUND_PROCESSOR=worker
      And 環境變數 WORKER_SERVICE_URL 未設定
      When 用戶 alice 觸發排程（catch EnqueueFailedError 流程）
      Then 該 resource status 變為 FAILED
      And 該 resource error_message 含 "背景處理排程失敗"

  @backend
  Rule: Watchdog 自動標記逾時 queued parse_job 為 FAILED
    Scenario: queued parse_job 超過 10 分鐘 → watchdog 標記 FAILED
      Given 一個 resource_parse_job status=queued 且 created_at 為 15 分鐘前
      When 執行 watchdog_dispatch_timeout()
      Then 該 parse_job status 變為 failed
      And 該 parse_job failure_reason 為 "dispatch timeout"
      And 對應 resource status 變為 FAILED

    Scenario: queued parse_job 未超過 10 分鐘 → watchdog 不修改
      Given 一個 resource_parse_job status=queued 且 created_at 為 5 分鐘前
      When 執行 watchdog_dispatch_timeout()
      Then 該 parse_job status 仍為 queued

    Scenario: watchdog 冪等 — 對已 FAILED parse_job 重跑無副作用
      Given 一個 resource_parse_job status=failed 且 created_at 為 20 分鐘前
      When 執行 watchdog_dispatch_timeout()
      Then 該 parse_job status 仍為 failed
