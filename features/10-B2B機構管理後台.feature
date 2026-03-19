@ignore
Feature: B2B機構管理後台

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                    | 訂閱方案 | 角色       |
      | 1        | admin@school.com         | ULTRA    | 機構管理員 |
      | 2        | teacher@school.com       | ULTRA    | 機構管理員 |
      | 3        | pro@example.com          | PRO      | 一般學員   |
      | 4        | student1@school.com      | FREE     | 學員       |
      | 5        | student2@school.com      | FREE     | 學員       |
    And 系統中有以下機構：
      | 機構 ID | 名稱       | 管理員 ID |
      | 1       | 志成補習班 | 1         |
    And 系統中有以下學員群組：
      | 群組 ID | 機構 ID | 名稱              | 成員數 |
      | 1       | 1       | AWS 雲端基礎班 A  | 2      |
      | 2       | 1       | PMP 衝刺班 B      | 0      |
    And 群組 1 包含以下學員：
      | 學員 ID | Email               |
      | 4       | student1@school.com |
      | 5       | student2@school.com |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 管理後台功能僅限 ULTRA 方案的機構管理員存取

    Example: PRO 方案用戶無法存取管理後台
      When 使用者 "pro@example.com" 嘗試存取機構管理後台
      Then 操作失敗
      And 錯誤訊息應為 "此功能僅限 ULTRA 方案用戶使用"

    Example: 非機構管理員角色無法存取管理後台
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                    | 訂閱方案 | 角色 |
        | 6        | ultra_student@school.com | ULTRA    | 學員 |
      When 使用者 "ultra_student@school.com" 嘗試存取機構管理後台
      Then 操作失敗
      And 錯誤訊息應為 "您沒有機構管理員權限"

  Rule: 前置（參數）- CSV 匯入檔案格式必須符合系統範本

    Example: 上傳欄位缺失的 CSV 檔案匯入失敗
      When 使用者 "admin@school.com" 上傳以下格式錯誤的 CSV 進行學員匯入：
        | 姓名   | 電子郵件         |
        | 王大明 | wang@example.com |
      Then 操作失敗
      And 錯誤訊息應為 "CSV 格式錯誤，請使用系統提供的範本（需包含姓名、電子郵件、群組欄位）"

    Example: 上傳包含重複 Email 的 CSV 檔案匯入失敗
      When 使用者 "admin@school.com" 上傳以下 CSV 進行學員匯入：
        | 姓名   | 電子郵件         | 群組             |
        | 王大明 | wang@example.com | AWS 雲端基礎班 A |
        | 王大明 | wang@example.com | AWS 雲端基礎班 A |
      Then 操作失敗
      And 錯誤訊息應為 "CSV 中包含重複的電子郵件：wang@example.com"

  # ========== 後置條件 ==========

  Rule: 後置（狀態）- 成功 CSV 匯入後應為每位新學員建立帳號並發送啟用邀請信

    Example: 合法 CSV 批量匯入學員後建立帳號並發送邀請
      When 使用者 "admin@school.com" 上傳以下合法 CSV 進行學員匯入：
        | 姓名   | 電子郵件          | 群組        |
        | 李小美 | li@example.com    | PMP 衝刺班 B |
        | 陳文哲 | chen@example.com  | PMP 衝刺班 B |
      Then 操作成功
      And 系統應建立 2 個新學員帳號
      And 系統應發送帳號啟用邀請信至以下 Email：
        | Email            |
        | li@example.com   |
        | chen@example.com |
      And 群組 "PMP 衝刺班 B" 的成員數應更新為 2

  Rule: 前置（狀態）- 匯入學籍名單前必須同意個資法與未成年人資料代為處理宣告

    Example: 機構管理員匯入名單未同意個資規範失敗
      When 使用者 "admin@school.com" 上傳合法 CSV 進行學員匯入，但未勾選同意「學員資料處理條款」
      Then 操作失敗
      And 錯誤訊息應為 "您必須聲明已取得相關當事人（包含未成年人之法定代理人）之同意，才可將資料匯入本系統"

  Rule: 後置（狀態）- 成功派發考卷後指定群組的學員應在有效期限內看到待完成測驗

    Example: 機構管理員向群組派發測驗並設定截止日期
      Given 系統中有以下機構考卷：
        | 考卷 ID | 機構 ID | 名稱              | 狀態 |
        | 1       | 1       | AWS SAA 月考試題  | 就緒 |
      When 使用者 "admin@school.com" 將考卷 1 派發給群組 1，截止日期為 2024-02-15
      Then 操作成功
      And 群組 1 的所有學員應看到待完成的測驗任務，截止日為 2024-02-15
      And 派發任務應記錄以下資訊：
        | 欄位     | 值               |
        | 目標群組 | AWS 雲端基礎班 A |
        | 考卷名稱 | AWS SAA 月考試題 |
        | 截止日期 | 2024-02-15       |

  Rule: 後置（回應）- 班級分析應回傳各知識節點的群組答對率熱點圖資料

    Example: 機構管理員查看班級弱點分析取得熱點圖資料
      When 使用者 "admin@school.com" 查看群組 1 的班級弱點分析
      Then 操作成功
      And 回應應包含以下熱點圖資料結構：
        | 欄位     | 說明                                      |
        | X 軸     | 各知識章節名稱清單                        |
        | Y 軸     | 各學員群組名稱清單                        |
        | 格子顏色 | 依答對率深淺著色（0%-100% 對應顏色深淺）  |

  Rule: 後置（回應）- 全班錯題排行榜應回傳答錯率最高的前 10 道題目

    Example: 機構管理員查看本週全班錯題排行榜
      When 使用者 "admin@school.com" 查看機構 1 本週全班錯題排行榜
      Then 操作成功
      And 回應應包含最多 10 道答錯率最高的題目
      And 每道題目應包含：
        | 欄位     | 說明             |
        | 題目內容 | 題目原文         |
        | 答錯率   | 全班答錯的百分比 |
        | 知識節點 | 所屬知識章節     |
