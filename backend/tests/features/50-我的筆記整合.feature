@feature_50 @user_notes @backend
Feature: 我的筆記整合後端契約
  覆蓋 Feature 50：使用者自由格式筆記 CRUD、chat_annotations PATCH、scaffold PATCH user_response。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And 已存在 FREE 用戶 "bob@example.com"
    And 已存在科目 "資安技術員" subject_id 存於 memo["subject_id"]
    And 已存在知識節點 "密碼學基礎" node_id 存於 memo["node_id"]，屬於該科目

  @backend
  Rule: 建立筆記 (POST /api/v1/user-notes)

    Scenario: Happy path — alice 建立科目層級筆記（無 node_id）
      When alice POST /api/v1/user-notes 含 subject_id 和 content "這是一篇科目層級的自由筆記，覆蓋重要概念"
      Then response status 為 201
      And note response 含欄位 id, user_id, subject_id, content, created_at, updated_at
      And DB 中 user_notes 新增一筆，node_id 為 null

    Scenario: Happy path — alice 建立節點綁定筆記（含 node_id）
      When alice POST /api/v1/user-notes 含 subject_id、node_id 和 content "密碼學重點整理"
      Then response status 為 201
      And response body node_id 不為 null

    Scenario: content 為空字串 → 422
      When alice POST /api/v1/user-notes 含空 content
      Then response status 為 422

    Scenario: subject_id 不存在 → 404
      When alice POST /api/v1/user-notes 含不存在的 subject_id 和 content "無效科目的筆記"
      Then response status 為 404

  @backend
  Rule: 列出筆記 (GET /api/v1/user-notes)

    Scenario: 列出自己所有筆記
      Given alice 已建立 3 筆不同科目的筆記
      When alice GET /api/v1/user-notes
      Then response status 為 200
      And list response 含欄位 items, total
      And items 筆數 >= 3

    Scenario: 依 subject_id 過濾筆記
      Given alice 已建立 2 筆屬於 subject_id 的筆記
      When alice GET /api/v1/user-notes?subject_id=<subject_id>
      Then response status 為 200
      And 所有 items 的 subject_id 均相同

    Scenario: bob 無法看到 alice 的筆記
      Given alice 已建立 1 筆筆記 id 存於 memo["note_id"]
      When bob GET /api/v1/user-notes
      Then response status 為 200
      And items 筆數 = 0

  @backend
  Rule: 更新筆記 (PATCH /api/v1/user-notes/{id})

    Scenario: alice 更新自己的筆記 content
      Given alice 已建立 1 筆筆記 id 存於 memo["note_id"]
      When alice PATCH /api/v1/user-notes/<note_id> 含 content "更新後的筆記內容，超過一個字元"
      Then response status 為 200
      And response body content 等於 "更新後的筆記內容，超過一個字元"

    Scenario: bob 更新 alice 的筆記 → 403
      Given alice 已建立 1 筆筆記 id 存於 memo["alice_note_id"]
      When bob PATCH /api/v1/user-notes/<alice_note_id> 含 content "試圖篡改他人筆記"
      Then response status 為 403

    Scenario: 更新不存在的筆記 → 404
      When alice PATCH /api/v1/user-notes/<nonexistent_id> 含 content "找不到的筆記更新"
      Then response status 為 404

  @backend
  Rule: 刪除筆記 (DELETE /api/v1/user-notes/{id})

    Scenario: alice 刪除自己的筆記
      Given alice 已建立 1 筆筆記 id 存於 memo["note_id"]
      When alice DELETE /api/v1/user-notes/<note_id>
      Then response status 為 204
      And DB 中該筆記已不存在

    Scenario: bob 刪除 alice 的筆記 → 403
      Given alice 已建立 1 筆筆記 id 存於 memo["alice_note_id"]
      When bob DELETE /api/v1/user-notes/<alice_note_id>
      Then response status 為 403

  @backend
  Rule: 更新 chat_annotation (PATCH /api/v1/chat-annotations/{id})

    Scenario: alice 更新自己的 annotation user_annotation
      Given alice 有一個 ai_chat_session 且包含一則 AI 訊息
      And alice 已建立一筆 annotation id 存於 memo["annotation_id"]
      When alice PATCH /api/v1/chat-annotations/<annotation_id> 含 user_annotation "更新後的評語內容，超過十個字元有效"
      Then response status 為 200
      And response body user_annotation 等於 "更新後的評語內容，超過十個字元有效"

    Scenario: PATCH annotation user_annotation 少於 10 字 → 422
      Given alice 有一個 ai_chat_session 且包含一則 AI 訊息
      And alice 已建立一筆 annotation id 存於 memo["annotation_id"]
      When alice PATCH /api/v1/chat-annotations/<annotation_id> 含 user_annotation "太短"
      Then response status 為 422

  @backend
  Rule: 更新 scaffold user_response (PATCH /api/v1/knowledge-map/scaffolds/{id})

    Scenario: alice 更新自己資源的 scaffold user_response
      Given alice 有一個資源 resource_id 存於 memo["resource_id"]
      And 該資源有一個 scaffold id 存於 memo["scaffold_id"]
      When alice PATCH /api/v1/knowledge-map/scaffolds/<scaffold_id> 含 user_response "這是我對此鷹架的詳細回應練習"
      Then response status 為 200
      And DB 中 scaffold 的 user_response 已更新

    Scenario: bob 更新 alice 的 scaffold → 403
      Given alice 有一個資源 resource_id 存於 memo["resource_id"]
      And 該資源有一個 scaffold id 存於 memo["scaffold_id"]
      When bob PATCH /api/v1/knowledge-map/scaffolds/<scaffold_id> 含 user_response "試圖修改他人鷹架"
      Then response status 為 403

  @backend
  Rule: 科目層級鷹架列表 (GET /api/v1/knowledge-map/subjects/{id}/scaffolds)

    Scenario: alice 在 2 個資源各寫 user_response，subject-level API 跨 resource 合併回傳
      Given alice 在科目下有 resource1 寫了 1 筆 user_response、resource2 寫了 2 筆 user_response
      When alice GET /api/v1/knowledge-map/subjects/<subject_id>/scaffolds?user_response_only=true
      Then response status 為 200
      And subject scaffold response 含 total=3 且 items 長度為 3

    Scenario: FREE 用戶無法讀科目層級鷹架 → 403
      When bob GET /api/v1/knowledge-map/subjects/<subject_id>/scaffolds?user_response_only=true
      Then response status 為 403

    Scenario: 不存在的 subject_id → 404
      When alice GET /api/v1/knowledge-map/subjects/<nonexistent_subject_id>/scaffolds
      Then response status 為 404
