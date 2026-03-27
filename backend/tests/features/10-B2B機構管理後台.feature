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
