@feature_49 @chat_annotations @backend
Feature: AI 教練對話 highlight + 強制評語（後端契約）
  覆蓋 Feature 49：使用者對 AI 訊息片段做 highlight，並附上評語（≥10字）儲存為 annotation。
  支援類型：note / key_insight / challenge / example / application。
  每個 session 最多 5 筆；只能標記自己的 session。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And 已存在 FREE 用戶 "bob@example.com"

  @backend
  Rule: 建立 annotation

    Scenario: Happy path — 對 AI 訊息 highlight 並寫評語 ≥10 字
      Given alice 有一個 ai_chat_session 且包含一則 AI 訊息
      When alice POST /api/v1/chat-annotations 含 highlighted_text 與 user_annotation "這個概念幫助我理解了機器學習的基礎，非常清楚"
      Then response status 為 201
      And response body 含 "id", "message_id", "session_id", "annotation_type"
      And DB 中 chat_message_annotations 新增一筆

    Scenario: annotation 少於 10 字 → 422
      Given alice 有一個 ai_chat_session 且包含一則 AI 訊息
      When alice POST /api/v1/chat-annotations 含 user_annotation "太短"
      Then response status 為 422

    Scenario: 跨 user 標他人對話 → 403
      Given alice 有一個 ai_chat_session 且包含一則 AI 訊息
      When bob POST /api/v1/chat-annotations 用 alice 的 session_id
      Then response status 為 403

    Scenario: 同 session 第 6 筆 → 409 上限
      Given alice 有一個 ai_chat_session 且包含一則 AI 訊息
      And alice 已在該 session 建立 5 筆 annotations
      When alice POST /api/v1/chat-annotations 第 6 筆
      Then response status 為 409
      And response detail 含 "上限"

  @backend
  Rule: 查詢 annotations

    Scenario: 列出自己的 annotations 並可 filter session_id
      Given alice 有兩個 ai_chat_session 各含一則 AI 訊息
      And alice 在 session_1 建立 2 筆 annotations
      And alice 在 session_2 建立 1 筆 annotation
      When alice GET /api/v1/chat-annotations
      Then response status 為 200
      And response 的 total 為 3
      When alice GET /api/v1/chat-annotations?session_id=<session_1_id>
      Then response 的 total 為 2

  @backend
  Rule: 刪除 annotation

    Scenario: 刪除自己的 annotation 回 204
      Given alice 有一個 ai_chat_session 且包含一則 AI 訊息
      And alice 已建立一筆 annotation
      When alice DELETE /api/v1/chat-annotations/<annotation_id>
      Then response status 為 204
      And DB 中該筆 annotation 已刪除

    Scenario: 刪除他人的 annotation → 403
      Given alice 有一個 ai_chat_session 且包含一則 AI 訊息
      And alice 已建立一筆 annotation
      When bob DELETE /api/v1/chat-annotations/<alice_annotation_id>
      Then response status 為 403
