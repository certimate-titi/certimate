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
