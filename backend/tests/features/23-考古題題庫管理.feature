@command
Feature: 考古題題庫管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案     | 角色         |
      | 1        | admin@example.com  | ULTRA_1599   | SUPER_ADMIN  |
      | 2        | user@example.com   | PRO_199      | USER         |
    And 系統中有以下考科分類：
      | 分類 ID | 名稱               |
      | 1       | 金融                |
      | 2       | IT                  |
      | 3       | 語言                |
      | 4       | 醫療                |
      | 5       | 公務員              |
    And 系統中有以下考科：
      | 考科 ID | 分類 ID | 名稱                          | is_popular |
      | 1       | 1       | 證券商業務員                   | true       |
      | 2       | 1       | 期貨商業務員                   | true       |
      | 3       | 2       | AI 應用規劃師                  | true       |
      | 4       | 2       | AWS SAA                        | true       |
      | 5       | 2       | AWS SAP                        | false      |
      | 6       | 2       | GCP ACE                        | true       |
      | 7       | 2       | Azure AZ-900                   | false      |
      | 8       | 1       | CFA Level 1                    | true       |
      | 9       | 3       | TOEIC                          | true       |
      | 10      | 3       | JLPT N1                        | false      |
      | 11      | 4       | 護理師                         | true       |
      | 12      | 5       | 普考                           | false      |
      | 13      | 1       | 不動產經紀人                   | true       |

  # ========== 考科 Seed ==========

  Rule: 命令（管理）- 管理員可匯入考科清單

    Example: 管理員 seed 考科到資料庫
      When 管理員 "admin@example.com" 執行考科 seed：
        | 分類       | 考科列表                         |
        | 金融證照   | 信託業業務人員, 理財規劃人員       |
      Then 操作應成功
      And 系統中應有考科 "信託業業務人員" 歸屬分類 "金融證照"

  # ========== 考古題匯入 ==========

  Rule: 命令（匯入）- 系統可從考古題 JSON 批次匯入題目

    Example: 匯入考古題 JSON 到題庫
      Given 考科 "證券商業務員" 有以下考古題資源：
        | 資源名稱                  | 狀態      |
        | 證券商業務員考古題題庫      | COMPLETED |
      And 資源 "證券商業務員考古題題庫" 有以下知識節點：
        | 節點名稱                 | 可出題數 |
        | 證券交易相關法規與實務     | 100     |
        | 企業內部控制              | 80      |
      When 系統匯入考古題 JSON 到考科 "證券商業務員"：
        | 題目數 | 有答案數 | Bloom 分佈                     |
        | 180    | 180      | remember:140, apply:20, analyze:20 |
      Then 操作應成功
      And 考科 "證券商業務員" 的題庫應有 180 題
      And 所有匯入的題目應有 historical_source 標記

  # ========== 考古題抽題 ==========

  Rule: 後置（抽題）- 當使用者建立測驗時，系統應優先從考古題題庫抽取

    Example: 選擇有考古題的知識節點時應從題庫抽取而非 AI 生成
      Given 使用者 "user@example.com" 有學習歷程於考科 "AI 應用規劃師"
      And 考科 "AI 應用規劃師" 有 213 題考古題
      When 使用者 "user@example.com" 提交測驗設定：
        | 欄位            | 值                                          |
        | node_ids        | [人工智慧基礎概論, 生成式AI應用與規劃]          |
        | question_count  | 20                                           |
        | difficulty      | 2                                            |
      Then 操作應成功
      And 測驗應包含 20 題
      And 所有題目應來自考古題題庫（historical_source 非空）
      And 題目應為隨機抽取（非固定順序）

    Example: 考古題不足時混合 AI 生成補充
      Given 使用者 "user@example.com" 有學習歷程於考科 "AI 應用規劃師"
      And 考科 "AI 應用規劃師" 知識節點 "機器學習技術與應用" 僅有 5 題考古題
      When 使用者 "user@example.com" 提交測驗設定：
        | 欄位            | 值                     |
        | node_ids        | [機器學習技術與應用]     |
        | question_count  | 20                     |
      Then 操作應成功
      And 測驗應包含 20 題
      And 至少 5 題應來自考古題題庫
      And 其餘題目由 AI 生成補充

  # ========== 題庫查詢 ==========

  Rule: 查詢 - 使用者可查看考科的題庫統計

    Example: 查詢考科題庫 Bloom 分佈
      When 使用者 "user@example.com" 查詢考科 "證券商業務員" 的題庫統計
      Then 操作應成功
      And API 回應應包含：
        | 欄位                | 值        |
        | total_questions     | 180       |
        | bloom_distribution  | (非空)    |
        | answer_rate         | (非空)    |

  # ========== 信度標示 ==========

  Rule: 後置（標示）- 每道題目應有信度標示

    Example: 考古題標記為高信度
      Given 題庫中有一道考古題（historical_source 非空）
      When 查詢該題目的信度標示
      Then 信度應為 "green"（🟢 考古題）

    Example: AI 生成題標記為中信度
      Given 題庫中有一道 AI 生成題（historical_source 為空）
      When 查詢該題目的信度標示
      Then 信度應為 "yellow"（🟡 AI 模擬題）

  # ========== 備考科目清單過濾 ==========

  Rule: 前置（過濾）- 新增備考科目清單只顯示有官方考古題的科目

    Example: 只有官方考古題的科目才出現在可選清單
      Given 考科 "證券商業務員" 有 100 題官方考古題（historical_source 非空）
      And 考科 "AWS SAA" 只有 AI 生成題（historical_source 為空）
      And 考科 "GCP ACE" 沒有任何題目
      When 使用者 "user@example.com" 查詢可選備考科目清單
      Then 操作應成功
      And 可選科目清單應包含 "證券商業務員"
      And 可選科目清單不應包含 "AWS SAA"
      And 可選科目清單不應包含 "GCP ACE"

    Example: 科目的可用題數應只計算官方考古題
      Given 考科 "AI 應用規劃師（初級）" 有 110 題官方考古題和 26 題 AI 生成題
      When 使用者 "user@example.com" 查詢可選備考科目清單
      Then 操作應成功
      And 科目 "AI 應用規劃師（初級）" 的可用題數應為 110
