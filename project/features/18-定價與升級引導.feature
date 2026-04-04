@ignore @query
Feature: 定價比較頁與升級引導

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案      |
      | 1        | free@example.com   | FREE          |
      | 2        | pro@example.com    | PRO_199       |
      | 3        | ultra@example.com  | ULTRA_1599    |
    And 系統中有以下方案定義：
      | 方案          | 月費  | AI 對話/日 | 上傳/月 | 考試/月 | Vision OCR/月 | 高階教練 | 自主出題 |
      | FREE          | 0     | 3          | 5       | 10      | 0             | 否       | 是       |
      | PRO_199       | 199   | 30         | 50      | 100     | 0             | 否       | 是       |
      | PRO_PLUS_399  | 399   | 200        | 200     | 500     | 50            | 是       | 是       |
      | ULTRA_1599    | 1599  | 無限       | 無限    | 無限    | 500           | 是       | 是       |
      | EDU           | 0     | 5          | 0       | 無限    | 0             | 否       | 否       |

  # ========== 定價比較頁 ==========

  Rule: 後置（回應）- 定價頁應回傳所有方案的功能比較矩陣

    Example: 未登入訪客查看定價頁取得方案比較
      When 訪客瀏覽定價比較頁
      Then 操作成功
      And 回應應包含 4 個可訂閱方案（FREE、PRO_199、PRO_PLUS_399、ULTRA_1599）
      And 每個方案應包含：
        | 欄位             | 說明                   |
        | plan_name        | 方案名稱               |
        | monthly_fee      | 月費金額               |
        | features         | 功能清單               |
        | cta_text         | CTA 按鈕文字           |
        | is_popular       | 是否為推薦方案（布林） |

    Example: 已登入用戶查看定價頁時標記當前方案
      When 使用者 "pro@example.com" 瀏覽定價比較頁
      Then 操作成功
      And PRO_199 方案應標記為「目前方案」
      And ULTRA_1599 方案的 CTA 應為「升級」或「免費試用 14 天」

  Rule: 後置（回應）- 定價頁應包含 EDU 方案說明區塊

    Example: 定價頁底部顯示教育機構方案說明
      When 訪客瀏覽定價比較頁
      Then 操作成功
      And 回應應包含教育方案說明區塊：
        | 欄位          | 說明                                     |
        | title         | 教育機構方案                             |
        | description   | ULTRA 方案含 30 名學生，適合補習班與老師 |
        | cta_text      | 聯絡我們 或 免費試用 14 天               |

  # ========== Paywall 升級引導 ==========

  Rule: 後置（回應）- 觸及功能限制時應回傳升級引導資訊

    Example: FREE 用戶觸及每日 AI 對話上限時收到升級引導
      Given 使用者 "free@example.com" 今日已使用 AI 對話 3 次
      When 使用者 "free@example.com" 發起第 4 次 AI 對話
      Then 操作失敗，錯誤為「已達今日 AI 對話上限」
      And 回應應包含升級引導：
        | 欄位           | 值                                    |
        | current_plan   | FREE                                  |
        | limit_type     | daily_ai_chat                         |
        | current_limit  | 3                                     |
        | upgrade_to     | PRO_199                               |
        | upgrade_limit  | 30                                    |
        | monthly_fee    | 199                                   |

    Example: PRO 用戶觸及每月上傳上限時收到升級引導
      Given 使用者 "pro@example.com" 本月已上傳 50 次
      When 使用者 "pro@example.com" 嘗試上傳第 51 份資源
      Then 操作失敗，錯誤為「已達本月上傳上限」
      And 回應應包含升級引導：
        | 欄位           | 值              |
        | current_plan   | PRO_199         |
        | limit_type     | monthly_uploads |
        | current_limit  | 50              |
        | upgrade_to     | PRO_PLUS_399    |
        | upgrade_limit  | 200             |
        | monthly_fee    | 399             |

  Rule: 後置（回應）- 點擊受限功能時應提示所需方案

    Example: FREE 用戶點擊高階教練功能收到方案提示
      When 使用者 "free@example.com" 嘗試使用高階教練功能
      Then 操作失敗，錯誤為「高階教練為 PRO_PLUS 以上方案專屬功能」
      And 回應應包含升級引導：
        | 欄位           | 值              |
        | required_plan  | PRO_PLUS_399    |
        | feature_name   | 高階教練        |

    Example: 非 ULTRA 用戶點擊教育管理後台收到方案提示
      When 使用者 "pro@example.com" 嘗試存取教育管理後台
      Then 操作失敗，錯誤為「此功能僅限 ULTRA 方案用戶使用」
      And 回應應包含升級引導：
        | 欄位           | 值              |
        | required_plan  | ULTRA_1599      |
        | feature_name   | 教育管理後台    |
        | trial_available| true            |

  # ========== 14 天試用引導 ==========

  Rule: 後置（回應）- 符合試用資格的用戶應在升級引導中看到試用選項

    Example: 未使用過試用的 FREE 用戶看到試用按鈕
      Given 使用者 "free@example.com" 從未使用過 ULTRA 免費試用
      When 使用者 "free@example.com" 瀏覽定價比較頁
      Then ULTRA_1599 方案應顯示「免費試用 14 天」CTA

    Example: 已使用過試用的用戶不顯示試用按鈕
      Given 使用者 "pro@example.com" 已使用過 ULTRA 免費試用
      When 使用者 "pro@example.com" 瀏覽定價比較頁
      Then ULTRA_1599 方案應顯示「升級」CTA（非「免費試用」）
