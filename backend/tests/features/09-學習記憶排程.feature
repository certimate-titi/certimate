@backend
Feature: 動態大腦精力調度排程

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 訂閱方案   |
      | 1        | alice@example.com    | FREE       |
      | 2        | proplus@example.com  | PRO_PLUS   |
    And 使用者 "proplus@example.com" 的備考科目設定如下：
      | 科目     | 考試日期   | 自評程度     |
      | AWS SAA  | 2026-04-08 | intermediate |
      | PMP      | 2026-09-15 | beginner     |
    And 使用者 "proplus@example.com" 在 AWS SAA 科目的答題統計如下：
      | 題目 ID | 知識節點    | 成功次數 | 失敗次數 | Ease Factor | 下次複習日   |
      | 101     | S3 儲存服務 | 2        | 5        | 1.3         | 2026-03-24   |
      | 102     | IAM 管理   | 10       | 1        | 2.5         | 2026-04-10   |
      | 103     | EC2 運算   | 0        | 0        | 2.5         | null         |
      | 104     | VPC 網路   | 3        | 3        | 1.8         | 2026-03-26   |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 使用者必須至少有一個備考科目才能使用排程

    Example: 無備考科目的使用者查看排程建議失敗
      Given 使用者 "alice@example.com" 尚未設定任何備考科目
      When 使用者 "alice@example.com" 查看學習排程建議
      Then 操作失敗，錯誤為「請先在 Onboarding 或會員中心新增至少一個備考科目」

  Rule: 前置（參數）- 排程初始化必須有考試日期

    Example: 考試日期未設定時無法初始化排程
      Given 使用者 "proplus@example.com" 的 AWS SAA 考試日期為空
      When 系統嘗試為使用者 "proplus@example.com" 的 AWS SAA 科目初始化排程
      Then 操作失敗，錯誤為「必須設定考試日期才能初始化排程」

  # ========== 模式自動推導 ==========

  Rule: 後置（狀態）- 系統應根據距考日天數自動推導學習模式

    Example: 距考日 14 天內自動推導為 Sprint 模式
      Given 今日為 2026-04-01
      When 系統為使用者 "proplus@example.com" 的 AWS SAA 科目計算學習模式
      Then 學習模式應為 "sprint"

    Example: 距考日 1 至 6 個月自動推導為 Standard 模式
      Given 使用者 "proplus@example.com" 的 PMP 考試日期為 2026-09-15
      And 今日為 2026-04-01
      When 系統為使用者 "proplus@example.com" 的 PMP 科目計算學習模式
      Then 學習模式應為 "standard"

    Example: 距考日超過 6 個月自動推導為 Mastery 模式
      Given 使用者 "proplus@example.com" 的 PMP 考試日期為 2027-06-01
      And 今日為 2026-04-01
      When 系統為使用者 "proplus@example.com" 的 PMP 科目計算學習模式
      Then 學習模式應為 "mastery"

  # ========== 查看排程建議 ==========

  Rule: 後置（回應）- 查看排程建議應回傳學習模式與推薦複習題

    Example: 有備考科目的使用者查看排程建議成功
      When 使用者 "proplus@example.com" 查看學習排程建議
      Then 操作成功
      And 回應應包含排程建議
