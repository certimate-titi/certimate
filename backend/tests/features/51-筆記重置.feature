@feature_51 @notes_reset @backend
Feature: 筆記重置後端契約
  覆蓋 Feature 51：user_notes/all、chat-annotations/all、scaffolds/reset-responses 三個重置端點。
  使用者只能重置自己的資料，互不影響。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And 已存在 FREE 用戶 "bob@example.com"
    And 已存在科目 "資安技術員" subject_id 存於 memo["subject_id"]
    And 已存在知識節點 "密碼學基礎" node_id 存於 memo["node_id"]，屬於該科目

  @backend
  Rule: 重置 user_notes (DELETE /api/v1/user-notes/all)

    Scenario: alice 有 5 筆 user_notes → 全刪 → 200 deleted=5 + DB 剩 0
      Given alice 已建立 5 筆 user_notes
      When alice DELETE /api/v1/user-notes/all
      Then response status 為 200
      And response body 含 deleted=5
      And DB 中 alice 的 user_notes 筆數為 0

    Scenario: alice 刪自己的 notes 不影響 bob 的 notes
      Given alice 已建立 2 筆 user_notes
      And bob 已建立 3 筆 user_notes
      When alice DELETE /api/v1/user-notes/all
      Then response status 為 200
      And DB 中 bob 的 user_notes 筆數為 3

    Scenario: alice 沒有 notes 時呼叫 → 200 deleted=0 不報錯
      When alice DELETE /api/v1/user-notes/all
      Then response status 為 200
      And response body 含 deleted=0

    Scenario: 未認證呼叫 DELETE /api/v1/user-notes/all → 401
      When 未認證 DELETE /api/v1/user-notes/all
      Then response status 為 401

  @backend
  Rule: 重置 chat_annotations (DELETE /api/v1/chat-annotations/all)

    Scenario: alice 有 3 筆 chat_annotations → 全刪 → 200 deleted=3 + DB 剩 0
      Given alice 已建立 3 筆 chat_annotations
      When alice DELETE /api/v1/chat-annotations/all
      Then response status 為 200
      And response body 含 deleted=3
      And DB 中 alice 的 chat_annotations 筆數為 0

    Scenario: alice 刪自己的 annotations 不影響 bob 的 annotations
      Given alice 已建立 1 筆 chat_annotations
      And bob 已建立 2 筆 chat_annotations
      When alice DELETE /api/v1/chat-annotations/all
      Then response status 為 200
      And DB 中 bob 的 chat_annotations 筆數為 2

    Scenario: alice 沒有 annotations 時呼叫 → 200 deleted=0 不報錯
      When alice DELETE /api/v1/chat-annotations/all
      Then response status 為 200
      And response body 含 deleted=0

    Scenario: 未認證呼叫 DELETE /api/v1/chat-annotations/all → 401
      When 未認證 DELETE /api/v1/chat-annotations/all
      Then response status 為 401

  @backend
  Rule: 重置 scaffold user_response (POST /api/v1/knowledge-map/scaffolds/reset-responses)

    Scenario: alice 在 2 個 resources 寫了 5 筆 user_response → reset → 200 cleared=5 + DB 全 NULL
      Given alice 有 2 個 resources 各含 user_response 的 scaffolds，共 5 筆有回應
      When alice POST /api/v1/knowledge-map/scaffolds/reset-responses
      Then response status 為 200
      And response body 含 cleared=5
      And DB 中 alice 的 scaffold user_response 全為 NULL

    Scenario: alice reset 不影響 bob 的 scaffold user_response
      Given alice 有 1 個 resource 含 2 筆 user_response scaffolds
      And bob 有 1 個 resource 含 2 筆 user_response scaffolds
      When alice POST /api/v1/knowledge-map/scaffolds/reset-responses
      Then response status 為 200
      And DB 中 bob 的 scaffold user_response 均不為 NULL

    Scenario: alice 沒有任何 user_response 時呼叫 → 200 cleared=0 不報錯
      When alice POST /api/v1/knowledge-map/scaffolds/reset-responses
      Then response status 為 200
      And response body 含 cleared=0

    Scenario: 未認證呼叫 POST /api/v1/knowledge-map/scaffolds/reset-responses → 401
      When 未認證 POST /api/v1/knowledge-map/scaffolds/reset-responses
      Then response status 為 401
