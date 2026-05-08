# language: zh-TW
@feature_41 @advance_organizer @concept_center @sprint_4_p3 @backend
Feature: 讀前定錨 + 概念中心（後端契約）
  覆蓋 Sprint 4 P3 T33-T39 後端：
  - migration 084 enum advance_organizer + concept_extract
  - K-06 v6 prompt 含 advance_organizer 規則
  - K-06-audio / K-06-image prompts
  - prompt routing 8 cases
  - seed_prompts content hash 比對

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @backend
  Rule: ResourceScaffoldType enum 6 種
    Scenario: enum 完整 6 種類別
      When 查 information_schema enum_range(NULL::resource_scaffold_type)
      Then 回傳 6 個值：takeaway / elaborative / strategy / pitfall / advance_organizer / concept_extract

    Scenario: 寫入 advance_organizer scaffold 不被 reject
      Given 用戶 "alice@example.com" 擁有資源 "res-41" 解析狀態為 "success"
      When _persist_parsed 處理 type=advance_organizer 鷹架
      Then resource_scaffolds 表新增 type='advance_organizer'
      And template_code='K-06-study'

  @backend
  Rule: K-06-audio + K-06-image prompts seed
    Scenario: 跑 seed_prompts → 7 個 K-06 模板全 sync
      When 執行 seed_prompts
      Then DB 含模板 IDs：
        | template_id     |
        | K-06            |
        | K-06-quiz       |
        | K-06-video      |
        | K-06-slides     |
        | K-06-notes      |
        | K-06-audio      |
        | K-06-image      |
      And template_id VARCHAR(32) 容得下 K-06-slides / K-06-video 長 ID

  @backend
  Rule: prompt seed content hash 比對
    Scenario: 同版本 + 同內容 → 跳過
      Given DB K-06 v6 內容與 file v6 相同
      When run_seed()
      Then K-06 被跳過 + log 含 "+ hash match"

    Scenario: 同版本 + 不同內容 → 自動 bump
      Given DB K-06 v3 內容（無 retrieval_prompt schema）
      And file K-06 v3 內容（含 retrieval_prompt schema）
      When run_seed()
      Then K-06 自動 bump 為 v4 並 sync file 內容
      And log 含 "🔄 內容 hash 不符自動更新"
      And new prompt_template_versions row created with change_note "Hash mismatch v3"

  @backend
  Rule: prompt routing 8 cases (含 audio + image)
    Scenario Outline: 全媒材 routing 正確
      Given resource gcs_path="<gcs>" / dct="<dct>" / yt="<yt>"
      When 呼叫 _select_prompt_template(resource)
      Then 回傳 "<template>"

      Examples:
        | gcs              | dct                | yt                   | template                |
        | x.pdf            |                    |                      | resource_parser_v2      |
        | x.pdf            | practice_questions |                      | resource_parser_quiz    |
        | x.mp4            |                    |                      | resource_parser_video   |
        |                  |                    | https://youtu.be/abc | resource_parser_video   |
        | x.pptx           |                    |                      | resource_parser_slides  |
        | x.docx           |                    |                      | resource_parser_notes   |
        | x.mp3            |                    |                      | resource_parser_audio   |
        | x.png            |                    |                      | resource_parser_image   |
