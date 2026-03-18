@ignore
Feature: 學習記憶排程

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 | Google Calendar 授權 |
      | 1        | alice@example.com  | FREE     | 未授權               |
      | 2        | bob@example.com    | PRO      | 已授權               |
      | 3        | carol@example.com  | ULTRA    | 已授權               |
    And 系統中有以下測驗錯題的記憶排程：
      | 排程 ID | 使用者 ID | 題目 ID | 建立日期   | 下次複習日 | 複習間隔（天） | 複習次數 |
      | 1       | 2        | 101     | 2024-01-10 | 2024-01-11 | 1              | 0        |
      | 2       | 2        | 102     | 2024-01-10 | 2024-01-13 | 3              | 1        |
      | 3       | 2        | 103     | 2024-01-03 | 2024-01-10 | 7              | 2        |
      | 4       | 3        | 201     | 2024-01-01 | 2024-01-15 | 14             | 3        |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- Google Calendar 整合需要使用者完成 OAuth 授權

    Example: 未授權 Google Calendar 的使用者啟用日曆同步失敗
      When 使用者 "alice@example.com" 嘗試啟用 Google Calendar 每日複習提醒
      Then 操作失敗
      And 錯誤訊息應為 "請先授權 Google Calendar 存取權限"

  # ========== 後置條件 ==========

  Rule: 後置（狀態）- 測驗後新答錯題目應自動建立艾賓浩斯初始排程

    Example: 提交測驗後系統為每道新錯題建立初始複習排程
      Given 使用者 "bob@example.com" 在 2024-01-20 提交測驗，並答錯以下題目：
        | 題目 ID | 題目內容                 |
        | 301     | VPC Peering 的限制為何？ |
      When 系統處理測驗錯題排程
      Then 題目 301 應建立以下初始排程：
        | 欄位       | 值         |
        | 建立日期   | 2024-01-20 |
        | 下次複習日 | 2024-01-21 |
        | 複習間隔   | 1 天       |
        | 複習次數   | 0          |

  Rule: 後置（狀態）- 完成複習後排程應依艾賓浩斯間隔序列 1/3/7/14/30 天遞增

    Scenario Outline: 完成指定複習次數後下次複習間隔遞增
      Given 使用者 "bob@example.com" 的題目排程目前複習次數為 <已複習次數>
      When 使用者 "bob@example.com" 完成該題目的複習並答對
      Then 下次複習間隔應更新為 <下次間隔> 天

      Examples:
        | 已複習次數 | 下次間隔 |
        | 0          | 3        |
        | 1          | 7        |
        | 2          | 14       |
        | 3          | 30       |
        | 4          | 30       |

  Rule: 後置（狀態）- 再次答錯同一題目時複習排程重置為間隔 1 天

    Example: 複習中再次答錯時排程重置
      Given 使用者 "bob@example.com" 的排程 2 目前複習間隔為 3 天，複習次數為 1
      When 使用者 "bob@example.com" 在複習排程中再次答錯題目 102
      Then 排程 2 的複習間隔應重置為 1 天
      And 排程 2 的複習次數應重置為 0
      And 排程 2 的下次複習日應更新為今日加 1 天

  Rule: 後置（狀態）- 授權 Google Calendar 後應在下次複習日建立每日複習行程

    Example: 已授權 Google Calendar 的用戶啟用日曆同步後自動建立行程
      When 使用者 "bob@example.com" 啟用 Google Calendar 每日複習提醒
      Then 操作成功
      And 系統應在 Google Calendar 中為 2024-01-11 建立以下行程：
        | 欄位 | 值                     |
        | 標題 | CertiMate 每日複習提醒 |
        | 說明 | 今日有 1 道題目排定複習 |

    Example: Google Calendar 行程包含可直接開啟複習的 Magic Link
      When 使用者 "bob@example.com" 啟用 Google Calendar 每日複習提醒
      Then 操作成功
      And 系統建立的 Google Calendar 行程應包含開啟今日複習測驗的連結
