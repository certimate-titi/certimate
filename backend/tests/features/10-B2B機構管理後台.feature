Feature: B2B 機構管理後台

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                    | 訂閱方案  | 角色       |
      | 1        | org-admin@school.com     | ULTRA     | ORG_ADMIN  |
      | 2        | teacher@school.com       | ULTRA     | ORG_ADMIN  |
      | 3        | pro@example.com          | PRO       | USER       |
      | 4        | student1@school.com      | FREE      | USER       |
      | 5        | student2@school.com      | FREE      | USER       |
    And 系統中有以下機構：
      | 機構 ID | 名稱       | 管理員 ID |
      | 1       | 志成補習班 | 1         |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 管理後台僅限 ULTRA 方案的機構管理員存取

    Example: PRO 方案用戶存取管理後台失敗
      When 使用者 "pro@example.com" 存取機構管理後台
      Then 操作失敗，錯誤為「此功能僅限 ULTRA 方案用戶使用」

  Rule: 前置（狀態）- 非機構管理員角色存取失敗

    Example: ULTRA 但非 org_admin 角色存取管理後台失敗
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                    | 訂閱方案 | 角色 |
        | 6        | ultra_student@school.com | ULTRA    | USER |
      When 使用者 "ultra_student@school.com" 存取機構管理後台
      Then 操作失敗，錯誤為「您沒有機構管理員權限」

  # ========== 機構資訊 ==========

  Rule: 後置（回應）- 機構管理員可查看機構資訊

    Example: 機構管理員查看機構資訊成功
      When 使用者 "org-admin@school.com" 存取機構管理後台
      Then 操作成功
      And 回應應包含機構名稱 "志成補習班"

  # ========== 空狀態 ==========

  @ignore
  Rule: 前置（狀態）- 機構尚無學員群組時應顯示空狀態引導

    Example: 機構無學員群組時查看學員列表返回空狀態
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                     | 訂閱方案 | 角色      |
        | 7        | new-admin@school.com      | ULTRA    | ORG_ADMIN |
      And 系統中有以下機構：
        | 機構 ID | 名稱         | 管理員 ID |
        | 2       | 新建補習班   | 7         |
      When 使用者 "new-admin@school.com" 查看機構 2 的學員列表
      Then 操作成功
      And 回應中學員列表應為空
      And 回應應包含空狀態提示「尚未匯入任何學員，請先透過 CSV 匯入學生名單」

    Example: 機構管理員首次進入管理後台時顯示初始化引導
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                     | 訂閱方案 | 角色      |
        | 8        | fresh-admin@school.com    | ULTRA    | ORG_ADMIN |
      And 系統中有以下機構：
        | 機構 ID | 名稱         | 管理員 ID |
        | 3       | 全新補習班   | 8         |
      When 使用者 "fresh-admin@school.com" 存取機構管理後台
      Then 操作成功
      And 回應應包含初始化引導資訊：
        | 欄位              | 說明                           |
        | has_students      | false                          |
        | has_groups        | false                          |
        | setup_steps       | 建立群組、匯入學員、派發考卷   |

  # ========== 學員搜尋與過濾 ==========

  @ignore
  Rule: 後置（回應）- 學員列表支援依名稱或 Email 搜尋過濾

    Example: 依學員名稱搜尋過濾學員列表
      When 使用者 "org-admin@school.com" 以關鍵字 "student1" 搜尋機構 1 的學員列表
      Then 操作成功
      And 回應應僅包含符合搜尋條件的學員
      And 回應中應包含學員 "student1@school.com"
      And 回應中不應包含學員 "student2@school.com"

    Example: 依 Email 搜尋過濾學員列表
      When 使用者 "org-admin@school.com" 以關鍵字 "student2@school.com" 搜尋機構 1 的學員列表
      Then 操作成功
      And 回應中應包含學員 "student2@school.com"

    Example: 搜尋無符合結果時回傳空列表
      When 使用者 "org-admin@school.com" 以關鍵字 "notexist" 搜尋機構 1 的學員列表
      Then 操作成功
      And 回應學員列表應為空

  # ========== 學員能力表展開 ==========

  @ignore
  Rule: 後置（回應）- 學員能力表展開應顯示 CompetencyBar 元件

    Example: 展開學員能力表顯示 CompetencyBar
      When 使用者 "org-admin@school.com" 展開學員 4 的能力表
      Then 操作成功
      And 回應應包含學員 ID 4 的能力列表
      And 每個能力節點應包含 CompetencyBar 所需資料：
        | 欄位       | 說明                                      |
        | label      | 知識節點名稱                              |
        | score      | 0-100 分                                  |
        | max_score  | 滿分值（固定 100）                         |
        | color      | green（>= 70）/ orange（40-69）/ red（< 40）|

  # ========== 班級弱點分析 ==========

  @ignore
  Rule: 後置（回應）- 班級弱點分析應回傳各知識節點的進度條資料

    Example: 查看班級弱點分析取得進度條資料
      When 使用者 "org-admin@school.com" 查看群組 1 的班級弱點分析
      Then 操作成功
      And 回應應包含各知識節點的弱點分析
      And 每個知識節點應包含進度條所需資料：
        | 欄位            | 說明                         |
        | node_name       | 知識節點名稱                 |
        | mastery_rate    | 掌握率（0-100）              |
        | student_count   | 未達標學員人數               |
        | total_students  | 群組總學員數                 |

  # ========== 未實作功能 Placeholder ==========

  @ignore
  Rule: 後置（回應）- 匯入學生名單按鈕顯示未實作提示

    Example: 點擊匯入學生名單按鈕顯示即將推出提示
      When 使用者 "org-admin@school.com" 在機構管理後台點擊「匯入學生名單」按鈕
      Then 系統應顯示提示訊息「此功能即將推出，敬請期待」

  @ignore
  Rule: 後置（回應）- 快速操作卡片點擊顯示未實作提示

    Example: 點擊快速操作卡片顯示即將推出提示
      When 使用者 "org-admin@school.com" 在機構管理後台點擊快速操作卡片
      Then 系統應顯示提示訊息「此功能即將推出，敬請期待」

  @ignore
  Rule: 後置（回應）- AI 個人化強化按鈕顯示未實作提示

    Example: 點擊 AI 個人化強化按鈕顯示即將推出提示
      When 使用者 "org-admin@school.com" 在學員能力檔案頁點擊「AI 個人化強化」按鈕
      Then 系統應顯示提示訊息「此功能即將推出，敬請期待」

  @ignore
  Rule: 後置（回應）- 指派補考按鈕顯示未實作提示

    Example: 點擊指派補考按鈕顯示即將推出提示
      When 使用者 "org-admin@school.com" 在學員詳情頁點擊「指派補考」按鈕
      Then 系統應顯示提示訊息「此功能即將推出，敬請期待」

  @ignore
  Rule: 後置（回應）- 匯出詳細報告按鈕顯示未實作提示

    Example: 點擊匯出詳細報告按鈕顯示即將推出提示
      When 使用者 "org-admin@school.com" 在班級分析頁點擊「匯出詳細報告」按鈕
      Then 系統應顯示提示訊息「此功能即將推出，敬請期待」
