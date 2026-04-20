@command
Feature: 考古題題庫管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案     | 角色         |
      | 1        | admin@example.com  | ULTRA_1599   | SUPER_ADMIN  |
      | 2        | user@example.com   | PRO_199      | USER         |
    And 系統中有以下考科分類：
      | 分類 ID | 名稱       |
      | 1       | 金融證照    |
      | 2       | 不動產證照  |
      | 3       | iPAS 產業人才鑑定 |
    And 系統中有以下考科：
      | 考科 ID | 分類 ID | 名稱           | is_popular |
      | 1       | 1       | 證券商業務員    | true       |
      | 2       | 1       | 期貨商業務員    | true       |
      | 3       | 3       | AI 應用規劃師   | true       |

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
  # ─────────────────────────────────────────────
  # PRD-033：平台預設資源綁定（subject_default_resources）
  # ─────────────────────────────────────────────
  @prd-033 @wip
  Rule: 管理員可綁定 platform 資源為考科預設資源

    Example: 管理員綁定預設資源
      Given 使用者 "admin@example.com" 角色為 "super_admin"
      And 存在 scope=platform 的資源 R_PLATFORM
      And 存在考科 S1 "AI 應用規劃師（初級）"
      When 呼叫 POST /api/v1/admin/subjects/{S1}/default-resources body={"resource_id": "R_PLATFORM"}
      Then 操作成功
      And subject_default_resources 應新增一筆 (subject_id=S1, resource_id=R_PLATFORM)

    Example: 使用者選該考科後自動看到預設資源
      Given 考科 S1 已綁定預設資源 R_PLATFORM
      And 使用者 "u1@example.com" 的備考科目包含 S1
      When 呼叫 GET /api/v1/resources
      Then 回應應包含 R_PLATFORM
      And R_PLATFORM 的 badge 應為 "official_default"
      And R_PLATFORM 的 is_readonly 應為 true

    Example: 管理員解除綁定
      When 呼叫 DELETE /api/v1/admin/subjects/{S1}/default-resources/{R_PLATFORM}
      Then 操作成功
      And 使用者 "u1@example.com" 的 GET /api/v1/resources 不再包含 R_PLATFORM
