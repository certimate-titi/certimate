@feature_54 @tags_3sources @backend
Feature: Tag 系統涵蓋 3 sources 後端契約
  覆蓋 Feature 54：hashtag tag 系統擴展至 3 sources：
  user_notes（user_note_tags）、chat_annotations（chat_annotation_tags）、
  scaffold user_response（scaffold_tags）。
  提供跨 3 sources 的聚合 API 與 items filter endpoint。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And 已存在 PRO 用戶 "bob@example.com"
    And 已存在科目 "資安技術員" subject_id 存於 memo["subject_id"]
    And 已存在科目 "人工智慧" second_subject_id 存於 memo["second_subject_id"]

  @backend
  Rule: chat annotation user_annotation 含 hashtag → chat_annotation_tags 寫入

    Scenario: create annotation 含 #深度學習 → chat_annotation_tags 寫入
      Given alice 已有 AI 對話 session_id 存於 memo["session_id"]，含一則訊息 message_id 存於 memo["message_id"]
      When alice POST /api/v1/chat-annotations with annotation text "這段提到 #深度學習 的概念"
      Then response status 為 201
      And DB 中 chat_annotation_tags 包含 annotation_id 對應的 tag_normalized "深度學習"

    Scenario: update annotation 改 user_annotation → tag diff 更新
      Given alice 已有 AI 對話 session_id 存於 memo["session_id"]，含一則訊息 message_id 存於 memo["message_id"]
      And alice 已建立含 "#舊標籤 是舊的內容" 的 annotation annotation_id 存於 memo["annotation_id"]
      When alice 更新 annotation user_annotation 為 "改成 #新標籤 的內容在這裡"
      Then response status 為 200
      And DB 中 chat_annotation_tags 包含 tag "新標籤"
      And DB 中 chat_annotation_tags 不含 tag "舊標籤"

    Scenario: delete annotation → cascade delete annotation tags
      Given alice 已有 AI 對話 session_id 存於 memo["session_id"]，含一則訊息 message_id 存於 memo["message_id"]
      And alice 已建立含 "#要刪除的標籤 annotation 測試內容" 的 annotation annotation_id 存於 memo["annotation_id"]
      When alice 刪除 memo["annotation_id"] 的 annotation
      Then response status 為 204
      And DB 中 chat_annotation_tags 對此 annotation_id 共 0 筆

  @backend
  Rule: scaffold PATCH user_response 含 hashtag → scaffold_tags 寫入

    Scenario: scaffold PATCH user_response 含 #線性代數 → scaffold_tags 寫入（含 user_id）
      Given alice 已有 resource_id 存於 memo["resource_id"]，含一個 scaffold scaffold_id 存於 memo["scaffold_id"]
      When alice 更新 scaffold user_response 為 "我學到 #線性代數 的應用" via API
      Then response status 為 200
      And DB 中 scaffold_tags 包含 scaffold_id 對應的 tag_normalized "線性代數" 且 user_id 為 alice

    Scenario: scaffold PATCH 更新 user_response → tag diff 更新
      Given alice 已有 resource_id 存於 memo["resource_id"]，含一個 scaffold scaffold_id 存於 memo["scaffold_id"]
      And alice 已 PATCH scaffold user_response 為 "#舊題目 的舊回答內容"
      When alice 更新 scaffold user_response 為 "新回答 #新題目 完全不同" via API
      Then response status 為 200
      And DB 中 scaffold_tags 包含 tag "新題目"
      And DB 中 scaffold_tags 不含 tag "舊題目"

    Scenario: delete scaffold → cascade delete scaffold tags
      Given alice 已有 resource_id 存於 memo["resource_id"]，含一個 scaffold scaffold_id 存於 memo["scaffold_id"]
      And alice 已 PATCH scaffold user_response 為 "#要刪除 scaffold cascade 測試"
      And DB 中已刪除該 scaffold
      Then DB 中 scaffold_tags 對此 scaffold_id 共 0 筆

  @backend
  Rule: aggregate endpoint 聚合 3 sources tags

    Scenario: 1 user 跨 3 sources 各寫 #AI → aggregate 回 count=3 sources breakdown
      Given alice 已建立含 "#AI 筆記內容測試" 的 user note note_id 存於 memo["note_id"]
      And alice 已有含 "#AI 的 annotation 標記十字元以上" 的 annotation（已建立）
      And alice 已有含 "#AI 的 scaffold 回答" 的 scaffold user_response（已建立）
      When alice GET /api/v1/user-tags/aggregate
      Then response status 為 200
      And response JSON 中 items 含 tag normalized="ai" count=3 sources breakdown {"note": 1, "annotation": 1, "scaffold": 1}

    Scenario: aggregate?subject_id= filter 只回該 subject 的 tags
      Given alice 已建立含 "#資安 筆記" 的 user note，subject_id 為 memo["subject_id"]
      And alice 已建立含 "#人工智慧 筆記" 的 user note，subject_id 為 memo["second_subject_id"]
      When alice GET /api/v1/user-tags/aggregate?subject_id={subject_id}
      Then response status 為 200
      And response JSON 中 items 含 tag normalized="資安"
      And response JSON 中 items 不含 tag normalized="人工智慧"

    Scenario: 跨 user 隔離 — alice tag 不出現在 bob aggregate
      Given alice 已建立含 "#alice專屬 筆記內容" 的 user note
      When bob GET /api/v1/user-tags/aggregate
      Then response status 為 200
      And response JSON 中 items 不含 tag normalized="alice專屬"

  @backend
  Rule: items endpoint 回傳 3 sources 混合 items

    Scenario: GET /user-tags/items?tag=ai 回傳 3 sources 混合 items
      Given alice 已建立含 "#AI 筆記內容測試" 的 user note note_id 存於 memo["note_id"]
      And alice 已有含 "#AI 的 annotation 標記十字元以上" 的 annotation（已建立）
      And alice 已有含 "#AI 的 scaffold 回答" 的 scaffold user_response（已建立）
      When alice GET /api/v1/user-tags/items?tag=ai
      Then response status 為 200
      And response JSON 中 items 含 _kind "note"
      And response JSON 中 items 含 _kind "annotation"
      And response JSON 中 items 含 _kind "scaffold"
      And response JSON 中 total 為 3

  @backend
  Rule: Obsidian export ZIP 涵蓋 3 sources

    Scenario: export ZIP 包含 3 sources 各自 .md（檔名前綴 note- annotation- scaffold-）
      Given alice 已有考後 31 天的學習旅程 journey_id 存於 memo["journey_id"]
      And alice 已建立含 "#考試 筆記" 的 user note
      And alice 已有含 "#考試 的 annotation 標記十字元以上" 的 annotation（已建立）
      And alice 已有含 "#考試 的 scaffold 回答" 的 scaffold user_response（已建立）
      When alice GET /api/v1/user-notes/export/obsidian?force=true
      Then response status 為 200
      And ZIP 中含有前綴為 "note-" 的 .md 檔案
      And ZIP 中含有前綴為 "annotation-" 的 .md 檔案
      And ZIP 中含有前綴為 "scaffold-" 的 .md 檔案

    Scenario: index.md tag 索引含 3 sources count breakdown
      Given alice 已有考後 31 天的學習旅程 journey_id 存於 memo["journey_id"]
      And alice 已建立含 "#複習 筆記" 的 user note
      And alice 已有含 "#複習 的 annotation 標記十字元以上" 的 annotation（已建立）
      When alice GET /api/v1/user-notes/export/obsidian?force=true
      Then response status 為 200
      And ZIP 中 index.md 含有 tag "#複習" 的 count breakdown（含 note: 和 annotation:）
