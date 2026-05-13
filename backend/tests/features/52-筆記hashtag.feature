@feature_52 @note_hashtags @backend
Feature: 筆記 hashtag 系統後端契約
  覆蓋 Feature 52：Obsidian-style `#word` hashtag 從 markdown content 解析，
  寫入 user_note_tags 表；支援 tag list API 與 tag filter 查詢。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And 已存在 FREE 用戶 "bob@example.com"
    And 已存在科目 "資安技術員" subject_id 存於 memo["subject_id"]
    And 已存在科目 "人工智慧" second_subject_id 存於 memo["second_subject_id"]
    And 已存在知識節點 "密碼學基礎" node_id 存於 memo["node_id"]，屬於該科目

  @backend
  Rule: create note 自動解析 hashtag

    Scenario: create note 含 #深度學習 和 #應用 → DB 寫 2 個 normalized tags
      When alice POST /api/v1/user-notes 含 content "#深度學習 概念定義 #應用"
      Then response status 為 201
      And DB 中 user_note_tags 包含 tag_normalized "深度學習" 與 "應用"

    Scenario: create note 含 markdown heading（# 後空格）→ 0 tags
      When alice POST /api/v1/user-notes 含 content "# 我是標題\n這裡沒有 hashtag"
      Then response status 為 201
      And DB 中 user_note_tags 對此 note 共 0 筆

    Scenario: tag normalization：#AI 和 #ai 同一 tag（normalized=ai）
      When alice POST /api/v1/user-notes 含 content "#AI 介紹 #ai 應用"
      Then response status 為 201
      And DB 中 user_note_tags 對此 note 共 1 筆，tag_normalized 為 "ai"

    Scenario: Unicode tag — #深度學習 #machine_learning #dl-101 全有效
      When alice POST /api/v1/user-notes 含 content "#深度學習 #machine_learning #dl-101 三種 tag"
      Then response status 為 201
      And DB 中 user_note_tags 包含 tag_normalized "深度學習" 與 "machine_learning" 與 "dl-101"

  @backend
  Rule: update note 增量 diff hashtag

    Scenario: update note 把 #深度學習 換成 #機器學習 → DB 移除 deeplearning 新增 ml
      Given alice 已建立含 "#深度學習 概念" 的筆記 id 存於 memo["note_id"]
      When alice PATCH /api/v1/user-notes/<note_id> 含 content "#機器學習 概念更新"
      Then response status 為 200
      And DB 中 user_note_tags 不含 tag_normalized "深度學習"
      And DB 中 user_note_tags 包含 tag_normalized "機器學習"

  @backend
  Rule: tag list API

    Scenario: list /user-notes/tags 回 user 所有 tags + count
      Given alice 已建立含各種 hashtag 的多筆筆記
      When alice GET /api/v1/user-notes/tags
      Then response status 為 200
      And tags list response 含欄位 items, total
      And items 至少含 1 筆 tag（normalized, display, count）

    Scenario: list /user-notes/tags?subject_id=X 只列該 subject 的 notes 用到的 tags
      Given alice 已建立 subject_id 科目的筆記含 "#資安標籤"
      And alice 已建立 second_subject_id 科目的筆記含 "#AI標籤"
      When alice GET /api/v1/user-notes/tags?subject_id=<subject_id>
      Then response status 為 200
      And tags items 只含 subject_id 科目的 tags，不含 "#AI標籤"

  @backend
  Rule: tag filter 查詢筆記

    Scenario: filter /user-notes?tag=深度學習 回所有含此 tag 的 notes
      Given alice 已建立含 "#深度學習 概念" 的筆記 id 存於 memo["note_id"]
      When alice GET /api/v1/user-notes?tag=深度學習
      Then response status 為 200
      And list response 含欄位 items, total
      And 所有 items 均含 tag "深度學習"

  @backend
  Rule: 跨 user 隔離

    Scenario: user B 看不到 user A 的 tags
      Given alice 已建立含 "#私密標籤" 的筆記
      When bob GET /api/v1/user-notes/tags
      Then response status 為 200
      And bob 的 tags items 不含 "私密標籤"

  @backend
  Rule: cascade delete

    Scenario: delete note → user_note_tags cascade 刪除
      Given alice 已建立含 "#要刪除的標籤" 的筆記 id 存於 memo["note_id"]
      When alice DELETE /api/v1/user-notes/<note_id>
      Then response status 為 204
      And DB 中 user_note_tags 對此 note 共 0 筆
