@feature_53 @obsidian_export @backend
Feature: Obsidian-compat markdown export 後端契約
  覆蓋 Feature 53：使用者可將自己的筆記匯出為 Obsidian-compatible ZIP 壓縮檔。
  ZIP 包含每張 user_note 一個 .md 檔（含 YAML frontmatter + content）以及 index.md 索引。

  B2 限制：只允許考後 30 天才能匯出，避免影響當下複習。
  例外：?force=true query param 可繞過。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And 已存在 FREE 用戶 "bob@example.com"
    And 已存在科目 "資安技術員" subject_id 存於 memo["subject_id"]

  @backend
  Rule: 考後 30 天才能匯出

    Scenario: 考試已結束 31 天的用戶可以匯出 ZIP
      Given alice 已有考後 31 天的學習旅程 journey_id 存於 memo["journey_id"]
      And alice 已建立 2 筆屬於 subject_id 的筆記
      When alice GET /api/v1/user-notes/export/obsidian
      Then response status 為 200
      And response content-type 為 application/zip
      And response body 為非空 bytes

    Scenario: 還在備考期的用戶嘗試匯出 → 403
      Given alice 已有未來考試的學習旅程（考試日 90 天後）
      When alice GET /api/v1/user-notes/export/obsidian
      Then response status 為 403
      And response JSON 含 message "考後 30 天才能匯出避免影響當下複習"

    Scenario: force=true 可繞過備考期限制
      Given alice 已有未來考試的學習旅程（考試日 90 天後）
      And alice 已建立 2 筆屬於 subject_id 的筆記
      When alice GET /api/v1/user-notes/export/obsidian?force=true
      Then response status 為 200
      And response content-type 為 application/zip

  @backend
  Rule: 0 筆 notes 仍回 200 ZIP

    Scenario: 無 notes 亦可匯出（空 ZIP）
      Given alice 已有考後 31 天的學習旅程 journey_id 存於 memo["journey_id"]
      When alice GET /api/v1/user-notes/export/obsidian
      Then response status 為 200
      And response content-type 為 application/zip

  @backend
  Rule: 跨 user 隔離

    Scenario: bob 只能匯出自己的筆記，看不到 alice 的筆記
      Given alice 已有考後 31 天的學習旅程 journey_id 存於 memo["journey_id"]
      And alice 已建立 2 筆屬於 subject_id 的筆記
      And bob 沒有任何筆記且已有考後 31 天的學習旅程
      When bob GET /api/v1/user-notes/export/obsidian
      Then response status 為 200
      And response content-type 為 application/zip
      And bob 的 ZIP 不含 alice 的筆記檔案
