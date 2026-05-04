@backend
Feature: 題目分類與考試趨勢分析

  # 注意：此 Feature 為後端 API 功能。Bloom 分佈統計由 GET /subjects/{id}/bloom-distribution 提供，
  # 前端消費點為 /exam/results 頁的 Bloom 認知層次分析區塊（已實作）。
  # 暫無獨立前端頁面規劃，改標記為 @backend。（2026-05-05 CEO 決議）

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案     |
      | 1        | pro@example.com    | PRO_199      |
      | 2        | ultra@example.com  | ULTRA_1599   |
    And 系統中有以下學科：
      | 學科 ID | 名稱               |
      | 1       | 信託業業務人員      |
      | 2       | 不動產經紀人        |
    And 系統中有以下歷年考古題（含 Bloom 分類）：
      | 題目 ID | 學科 ID | 年份 | 題型            | 難度   | Bloom 分類 |
      | 1       | 1       | 2022 | single_choice  | easy   | remember   |
      | 2       | 1       | 2022 | single_choice  | medium | understand |
      | 3       | 1       | 2022 | single_choice  | medium | apply      |
      | 4       | 1       | 2023 | single_choice  | hard   | analyze    |
      | 5       | 1       | 2023 | single_choice  | medium | evaluate   |
      | 6       | 2       | 2023 | single_choice  | easy   | remember   |

  # ========== Bloom 分類分佈查詢 ==========

  Rule: 前置（分析）- 系統提供各科目 Bloom 認知層次分佈統計

    Example: 查詢信託業業務人員歷年 Bloom 分佈
      When 使用者 "pro@example.com" 查詢學科 "信託業業務人員" 的 Bloom 分類統計
      Then 回應中應包含以下分佈：
        | bloom_category | count | percentage |
        | remember       | 1     | 20.0       |
        | understand     | 1     | 20.0       |
        | apply          | 1     | 20.0       |
        | analyze        | 1     | 20.0       |
        | evaluate       | 1     | 20.0       |
        | create         | 0     | 0.0        |

    Example: 跨年度趨勢分析顯示各年 Bloom 分佈變化
      When 使用者 "ultra@example.com" 查詢學科 "信託業業務人員" 的年度 Bloom 趨勢
      Then 回應中應包含 2022 年與 2023 年各自的 Bloom 分佈
      And 趨勢資料格式應為：
        | year | remember | understand | apply | analyze | evaluate | create |
        | 2022 | 1        | 1          | 1     | 0       | 0        | 0      |
        | 2023 | 0        | 0          | 0     | 1       | 1        | 0      |

  # ========== 智慧出題：依 Bloom 分佈出題 ==========

  Rule: 後置（出題）- 有考古題時自動套用其 Bloom 分佈；無考古題時使用預設配比

    Example: 科目有考古題時，自動依考古題 Bloom 分佈出 10 題（無需手動啟用）
      Given 學科 "信託業業務人員" 的歷年考古題 Bloom 統計為：
        | bloom_category | suggested_percentage |
        | remember       | 40                   |
        | understand     | 30                   |
        | apply          | 20                   |
        | analyze        | 7                    |
        | evaluate       | 2                    |
        | create         | 1                    |
      When 使用者 "pro@example.com" 提交測驗設定，選擇學科 "信託業業務人員"，題數為 10
      Then 系統應自動偵測該科目有考古題 Bloom 統計
      And 生成的 10 題中，各 Bloom 分類數量應符合考古題分佈（誤差 ±1 題）
      And exam 的 bloom_distribution 欄位應記錄實際分佈 JSON
      And exam 的 bloom_source 應為 "historical"

    Example: 科目無考古題時，使用系統預設 Bloom 配比
      Given 學科 "自創課程A" 無任何考古題資料
      When 使用者 "pro@example.com" 提交測驗設定，選擇學科 "自創課程A"，題數為 10
      Then 系統應套用預設 Bloom 配比：
        | bloom_category | default_percentage |
        | remember       | 20                 |
        | understand     | 25                 |
        | apply          | 25                 |
        | analyze        | 15                 |
        | evaluate       | 10                 |
        | create         | 5                  |
      And exam 的 bloom_source 應為 "default"

    Example: 使用者可手動覆寫自動套用的 Bloom 配比
      Given 學科 "信託業業務人員" 有考古題 Bloom 統計
      When 使用者 "ultra@example.com" 提交測驗設定，選擇學科 "信託業業務人員"，題數為 10，並手動指定 Bloom 配比為：
        | bloom_category | custom_percentage |
        | remember       | 10                |
        | understand     | 20                |
        | apply          | 30                |
        | analyze        | 20                |
        | evaluate       | 15                |
        | create         | 5                 |
      Then 生成的 10 題應依手動指定的配比出題（誤差 ±1 題）
      And exam 的 bloom_source 應為 "custom"

  # ========== 考試結果：Bloom 分析報告 ==========

  Rule: 後置（結果）- 測驗完成後提供 Bloom 各層次得分率

    Example: 測驗結果頁顯示各 Bloom 層次的答對率
      Given 使用者 "pro@example.com" 完成一場含 Bloom 分類的測驗
        | 題目 ID | Bloom 分類 | 作答結果 |
        | 1       | remember   | 正確     |
        | 2       | understand | 錯誤     |
        | 3       | apply      | 正確     |
      When 使用者查看測驗結果
      Then 結果中應包含 Bloom 層次分析：
        | bloom_category | correct | total | accuracy_rate |
        | remember       | 1       | 1     | 100.0         |
        | understand     | 0       | 1     | 0.0           |
        | apply          | 1       | 1     | 100.0         |
      And AI 教練應針對答錯的 "understand" 層次給予強化建議

  # ========== 考古題爬蟲：批次匯入 ==========

  Rule: 後置（匯入）- 管理員可批次匯入考古題並自動觸發 Bloom 分類

    Example: 管理員上傳考古題 JSON 後系統自動執行 Bloom 分類
      Given 管理員已上傳格式正確的考古題 JSON（50 題，bloom_category 為 null）
      When 管理員觸發「自動 Bloom 分類」
      Then 系統應呼叫 AI 分類服務，為每道題目填入 bloom_category
      And 50 題處理完成後，匯入結果應顯示各 Bloom 分類統計

    Example: 匯入的考古題格式不符 schema 時回傳錯誤
      Given 管理員上傳的考古題 JSON 缺少 correct_answer 欄位
      When 管理員觸發匯入
      Then 操作失敗
      And 錯誤訊息應為 "第 3 題缺少必填欄位：correct_answer"
