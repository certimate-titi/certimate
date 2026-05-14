@backend
Feature: 55 — Tag Backfill Admin Endpoint
  PR #96/#99 只對 create/update 觸發 hashtag parser；
  既有筆記 user_note_tags 為空。
  SUPER_ADMIN 呼叫 POST /admin/backfill-tags 後應補寫所有 hashtag tags，
  且同操作可重複執行（idempotent）。

  Background:
    Given 系統中已有使用者
      | email                    | role        |
      | alice@example.com        | USER        |
      | super@certimate.test     | SUPER_ADMIN |

  @backend
  Scenario: backfill 補寫既有 note 的 tag
    Given alice 有一筆 legacy note 含 "#深度學習" 但 user_note_tags 為空
    And super@certimate.test 已登入為 SUPER_ADMIN
    When POST /api/v1/admin/backfill-tags 由 super@certimate.test 呼叫
    Then 回應 200
    And result.user_notes_processed >= 1
    And user_note_tags 表對 memo["legacy_note_id"] 有 1 筆 tag_normalized="深度學習"

  @backend
  Scenario: backfill 可重複執行不重覆寫入（idempotent）
    Given alice 有一筆 legacy note 含 "#深度學習" 但 user_note_tags 為空
    And super@certimate.test 已登入為 SUPER_ADMIN
    When POST /api/v1/admin/backfill-tags 由 super@certimate.test 呼叫
    And POST /api/v1/admin/backfill-tags 由 super@certimate.test 呼叫
    Then user_note_tags 表對 memo["legacy_note_id"] 恰好有 1 筆 tag_normalized="深度學習"

  @backend
  Scenario: 非 SUPER_ADMIN 呼叫 backfill-tags 應回 403
    And super@certimate.test 已登入為 SUPER_ADMIN
    When POST /api/v1/admin/backfill-tags 由 alice@example.com 呼叫
    Then 回應 403
