@backend
Feature: F47 — YouTube Pipeline E2E（tasks endpoint 端到端）
  確保 YouTube 資源的 tasks/process-resource 不被 early-skip，
  且 ResourceChunk 與 resource_parse_jobs 實際寫入 DB。

  # memory feedback_e2e_upload_parse_bdd.md：動到 resource pipeline 的 PR 必補此類 e2e BDD

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                    | 訂閱方案 |
      | 1        | yt_e2e@example.com       | PRO      |
    And 使用者 "yt_e2e@example.com" 備考科目為 "計算機概論"（科目 ID: 1）

  Rule: YouTube resource 不被 gcs_path early-skip

  @backend
  Scenario: YT resource 觸發 process-resource 不因缺 gcs_path 而跳過
    Given 環境變數 BACKGROUND_PROCESSOR 設為 inline
    And 使用者 "yt_e2e@example.com" 有一筆 YouTube 資源（無 gcs_path）
    When 系統觸發 tasks/process-resource（mock document_processing + parse_job）
    Then tasks endpoint 回應 status 不為 skipped
    And tasks endpoint 回應 ok 為 true

  @backend
  Scenario: YT resource process-resource 完整 pipeline — ResourceChunk 寫入 DB
    Given 環境變數 BACKGROUND_PROCESSOR 設為 inline
    And 使用者 "yt_e2e@example.com" 有一筆 YouTube 資源（無 gcs_path）
    When 系統觸發 tasks/process-resource（mock document_processing 產生 chunk + mock parse_job 成功）
    Then resource_chunks 表對該資源至少有 1 筆記錄
    And resource_parse_jobs 表對該資源至少有 1 筆 SUCCESS 記錄
