# language: zh-TW
@feature_38 @scaffold_pitfall @prompt_routing @sprint_2_p1 @backend
Feature: 學習鷹架迷思警示與檔案分流（後端契約）
  覆蓋 Sprint 2 P1 T11-T18 後端：
  - migration 083 enum value pitfall
  - _build_scaffold_row 接受 pitfall + dedup
  - _select_prompt_template 路由邏輯

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @backend
  Rule: ResourceScaffoldType enum 含 pitfall
    Scenario: 寫入 pitfall scaffold 不被 enum reject
      Given 用戶 "alice@example.com" 擁有資源 "res-38" 解析狀態為 "success"
      And K-06 v5 解析回傳 scaffolds 含一筆 type=pitfall
      When _persist_parsed 處理該 scaffolds
      Then resource_scaffolds 表新增一筆 type='pitfall'
      And 該 row 的 retrieval_prompt 為 NULL
      And 該 row 的 template_code 為 'K-06-study'

    Scenario: pitfall scaffold dedup 同章節只保留一筆
      Given K-06 v5 LLM 回傳 4 筆 scaffolds，其中 2 筆 (chapter='3.1', type=pitfall)
      When _persist_parsed 處理該 scaffolds
      Then resource_scaffolds 表只有 1 筆 (chapter='3.1', type='pitfall')
      And 後端 log 含 "[pitfall-dedup] skip duplicate"

  @backend
  Rule: prompt routing 依檔案類型分流
    Scenario Outline: _select_prompt_template 路由
      Given resource gcs_path="<gcs>" 並 detected_content_type="<dct>" 並 youtube_url="<yt>"
      When 呼叫 _select_prompt_template(resource)
      Then 回傳 "<template>"

      Examples:
        | gcs                 | dct                | yt                          | template                |
        | uploads/test.pdf    |                    |                             | resource_parser_v2      |
        | uploads/test.pdf    | practice_questions |                             | resource_parser_quiz    |
        | uploads/lecture.mp4 |                    |                             | resource_parser_video   |
        | uploads/x.MOV       |                    |                             | resource_parser_video   |
        |                     |                    | https://youtu.be/abc        | resource_parser_video   |
        |                     |                    |                             | resource_parser_v2      |
        | uploads/x.jpg       |                    |                             | resource_parser_v2      |

  @backend
  Rule: prompt fallback
    Scenario: 特化模板不存在時 fallback 到 resource_parser_v2
      Given DB 中無 'resource_parser_video' 模板
      And resource gcs_path="uploads/x.mp4"
      When run_parse_job 啟動 _call_gemini_once
      Then prompt_service 嘗試 'resource_parser_video' 失敗
      And 自動 fallback 載入 'resource_parser_v2'
      And log 含 "fallback to resource_parser_v2"
