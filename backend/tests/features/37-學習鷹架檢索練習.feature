# language: zh-TW
@feature_37 @scaffold_retrieval @sprint_1_p0 @backend
Feature: 學習鷹架檢索練習（後端契約）
  覆蓋 Sprint 1 P0 T08 + T09 後端 endpoint。
  端對端 UX 測試在 project/features/37-學習鷹架檢索練習.feature。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"
    And 用戶 "alice@example.com" 擁有資源 "res-37" 且解析狀態為 "success"
    And 資源 "res-37" 含章節 "3.1 人工智慧概念" 對應 page_start=15 / page_end=25

  @backend
  Rule: retrieval_prompt 序列化
    Scenario: takeaway 鷹架必含 retrieval_prompt
      Given 資源 "res-37" 章節 "3.1 人工智慧概念" 含一筆 takeaway 鷹架
        | content                  | retrieval_prompt           |
        | AI 三層級分為 ANI/AGI/ASI | 想想看 — AI 三層級是什麼？  |
      When 用戶 "alice@example.com" 取得資源 "res-37" 的 /parsed
      Then 回應 200 且 scaffolds 中至少 1 筆 type=takeaway
      And 該 scaffold 的 retrieval_prompt 為 "想想看 — AI 三層級是什麼？"
      And 該 scaffold 的 template_code 為 "K-06-study"

    Scenario: strategy 鷹架 retrieval_prompt 為 null
      Given 資源 "res-37" 章節 "3.1 人工智慧概念" 含一筆 strategy 鷹架
      When 用戶 "alice@example.com" 取得資源 "res-37" 的 /parsed
      Then scaffolds 中所有 type=strategy 的項目 retrieval_prompt 為 null

  @backend
  Rule: 鷹架互動事件 log
    Scenario: 揭曉事件寫入 log
      Given 資源 "res-37" 含一筆 takeaway 鷹架 id="sf-1"
      When 用戶 "alice@example.com" POST /resource-scaffolds/sf-1/interactions {"event":"revealed"}
      Then 回應 200 含 log_id
      And scaffold_interaction_log 表新增一筆 (scaffold_id=sf-1, event=revealed)

    Scenario: 自評回想感事件寫入 log
      Given 資源 "res-37" 含一筆 takeaway 鷹架 id="sf-1"
      When 用戶 "alice@example.com" POST /resource-scaffolds/sf-1/interactions {"event":"recall_self_rated","recall_quality":"full"}
      Then 回應 200
      And scaffold_interaction_log 表新增一筆 (event=recall_self_rated, recall_quality=full)

    Scenario Outline: recall_quality 必為合法 enum
      When 用戶 POST /resource-scaffolds/sf-1/interactions {"event":"recall_self_rated","recall_quality":"<q>"}
      Then 回應 <code>

      Examples:
        | q         | code |
        | none      | 200  |
        | partial   | 200  |
        | full      | 200  |
        | invalid   | 422  |

    Scenario: recall_self_rated 缺 recall_quality 必拒絕
      When 用戶 POST /resource-scaffolds/sf-1/interactions {"event":"recall_self_rated"}
      Then 回應 422 含訊息 "requires recall_quality"

    Scenario: 非擁有者不能 log 互動
      Given 已存在另一用戶 "bob@example.com"
      When 用戶 "bob@example.com" POST /resource-scaffolds/sf-1/interactions {"event":"viewed"}
      Then 回應 403

  @backend
  Rule: 章節練習自動帶題（chapter-practice endpoint）
    Scenario: 章節有 page range + 對應題目 → 回 2-3 題
      Given 資源 "res-37" 在 page 15-25 範圍內有 2 題已核可題目
      When 用戶 "alice@example.com" GET /resources/res-37/chapter-practice?chapter_heading=3.1+人工智慧概念
      Then 回應 200
      And page_range 為 [15, 25]
      And questions 陣列長度為 2
      And 每題物件含 content / option_a / option_b / option_c / option_d / correct_answer

    Scenario: 章節無 page range → 回空陣列（合理空態）
      Given 章節 "目錄" 對應 scaffold 的 page_start 為 NULL
      When 用戶 "alice@example.com" GET /resources/res-37/chapter-practice?chapter_heading=目錄
      Then 回應 200
      And page_range 為 []
      And questions 陣列長度為 0

    Scenario: 非擁有者拒絕讀取
      Given 已存在另一用戶 "bob@example.com"
      When 用戶 "bob@example.com" GET /resources/res-37/chapter-practice?chapter_heading=3.1+人工智慧概念
      Then 回應 403

    Scenario: questions 上限 3 題
      Given 資源 "res-37" 在 page 15-25 範圍內有 5 題已核可題目
      When 用戶 "alice@example.com" GET /resources/res-37/chapter-practice?chapter_heading=3.1+人工智慧概念
      Then questions 陣列長度為 3
