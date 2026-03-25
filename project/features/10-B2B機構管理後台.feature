@ignore @command
Feature: B2B 機構管理後台

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                    | 訂閱方案      | 角色       |
      | 1        | org-admin@school.com     | ULTRA_1599    | org_admin  |
      | 2        | teacher@school.com       | ULTRA_1599    | org_admin  |
      | 3        | pro@example.com          | PRO_199       | user       |
      | 4        | student1@school.com      | FREE          | user       |
      | 5        | student2@school.com      | FREE          | user       |
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
    And 系統中有以下早期預警規則（機構 1）：
      | 最低平均分 | 最大連續下降次數 | 最大未登入天數 |
      | 60         | 3                | 5              |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 管理後台僅限 ULTRA 方案的機構管理員存取

    Example: PRO 方案用戶存取管理後台失敗
      When 使用者 "pro@example.com" 存取機構管理後台
      Then 操作失敗，錯誤為「此功能僅限 ULTRA 方案用戶使用」

    Example: ULTRA 但非 org_admin 角色存取管理後台失敗
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                    | 訂閱方案   | 角色 |
        | 6        | ultra_student@school.com | ULTRA_1599 | user |
      When 使用者 "ultra_student@school.com" 存取機構管理後台
      Then 操作失敗，錯誤為「您沒有機構管理員權限」

  Rule: 前置（參數）- CSV 匯入必須符合固定欄位格式（姓名、電子郵件、群組）

    Example: 上傳缺少欄位的 CSV 匯入失敗
      When 使用者 "org-admin@school.com" 上傳以下 CSV 進行學員匯入：
        | 姓名   | 電子郵件         |
        | 王大明 | wang@example.com |
      Then 操作失敗，錯誤為「CSV 格式錯誤，請使用系統提供的範本（需包含姓名、電子郵件、群組欄位）」

    Example: 上傳包含重複 Email 的 CSV 匯入失敗
      When 使用者 "org-admin@school.com" 上傳以下 CSV 進行學員匯入：
        | 姓名   | 電子郵件         | 群組             |
        | 王大明 | wang@example.com | AWS 雲端基礎班 A |
        | 王大明 | wang@example.com | AWS 雲端基礎班 A |
      Then 操作失敗，錯誤為「CSV 中包含重複的電子郵件：wang@example.com」

  Rule: 前置（狀態）- 匯入學員名單前必須同意個資處理條款

    Example: 未勾選個資同意即匯入失敗
      When 使用者 "org-admin@school.com" 上傳合法 CSV 進行學員匯入，但未勾選同意「學員資料處理條款」
      Then 操作失敗，錯誤為「您必須聲明已取得相關當事人之同意，才可將資料匯入本系統」

  # ========== CSV 匯入 ==========

  Rule: 後置（狀態）- 成功匯入後應建立帳號、發送邀請信並更新群組成員數

    Example: 合法 CSV 批量匯入學員成功
      When 使用者 "org-admin@school.com" 上傳以下合法 CSV 進行學員匯入：
        | 姓名   | 電子郵件          | 群組         |
        | 李小美 | li@example.com    | PMP 衝刺班 B |
        | 陳文哲 | chen@example.com  | PMP 衝刺班 B |
      Then 操作成功
      And 系統應建立 2 個新學員帳號
      And 系統應發送啟用邀請信至：
        | Email            |
        | li@example.com   |
        | chen@example.com |
      And 群組 "PMP 衝刺班 B" 的成員數應為 2

  # ========== 考卷派發 ==========

  Rule: 後置（狀態）- 派發考卷後群組學員應看到待完成測驗

    Example: 向群組派發考卷並設定截止日期
      Given 系統中有以下機構考卷設定：
        | 考卷 ID | 機構 ID | 名稱              | 狀態 |
        | 1       | 1       | AWS SAA 月考試題  | READY|
      When 使用者 "org-admin@school.com" 將考卷 1 派發給群組 1，截止日期為 "2026-04-15"
      Then 操作成功
      And 群組 1 的所有學員應看到待完成的測驗任務
      And 派發記錄應包含：
        | 欄位       | 值               |
        | group_name | AWS 雲端基礎班 A |
        | exam_name  | AWS SAA 月考試題 |
        | deadline   | 2026-04-15       |

  # ========== 班級分析 ==========

  Rule: 後置（回應）- 班級熱力圖應回傳知識節點 × 學員群組的答對率矩陣

    Example: 查看班級熱力圖取得答對率矩陣
      When 使用者 "org-admin@school.com" 查看群組 1 的班級熱力圖
      Then 操作成功
      And 回應應包含矩陣結構：
        | 欄位       | 說明                             |
        | x_axis     | 知識節點名稱列表                 |
        | y_axis     | 學員名稱列表                     |
        | cells      | 各格答對率（0-100），對應顏色深淺 |

  Rule: 後置（回應）- 全班錯題排行應回傳答錯率最高的前 10 題

    Example: 查看全班錯題排行取得 Top 10
      When 使用者 "org-admin@school.com" 查看機構 1 的全班錯題排行
      Then 操作成功
      And 回應應包含最多 10 筆題目
      And 每筆題目應包含：
        | 欄位          | 說明             |
        | question_text | 題目原文         |
        | error_rate    | 全班答錯百分比   |
        | node_name     | 所屬知識節點     |

  # ========== 班級健康 KPI ==========

  Rule: 後置（回應）- 班級健康 KPI 應回傳四項摘要數值

    Example: 查看班級健康 KPI
      When 使用者 "org-admin@school.com" 查看機構 1 的班級健康摘要
      Then 操作成功
      And 回應應包含：
        | 欄位           | 說明                                |
        | total          | 機構授權總學員數                    |
        | active_rate    | 過去 7 天有登入的學員比例（0.0-1.0）|
        | at_risk_count  | 符合預警條件的學員人數              |
        | avg_score      | 全班最近一次測驗平均分              |

  # ========== 早期預警 ==========

  Rule: 後置（回應）- 早期預警應依機構自訂閾值偵測需關注學員

    Example: 查看預警清單取得符合條件的學員
      Given 學員 "student2@school.com" 最近三次測驗平均分為 48
      When 使用者 "org-admin@school.com" 查看機構 1 的早期預警清單
      Then 操作成功
      And 回應中應包含學員 "student2@school.com"
      And 該學員資料應包含：
        | 欄位             | 值             |
        | student_id       | 5              |
        | name             | student2       |
        | avg_score        | 48             |
        | trend            | flat           |
        | weakest_topic    | 最弱知識節點   |
        | last_active_days | 0              |

  Rule: 後置（狀態）- 機構管理員可自訂預警閾值

    Example: 更新預警規則成功
      When 使用者 "org-admin@school.com" 更新機構 1 的預警規則，最低平均分為 50，最大連續下降次數為 2，最大未登入天數為 3
      Then 操作成功
      And 機構 1 的預警規則應為：
        | 欄位             | 值 |
        | min_avg_score    | 50 |
        | max_decline_trend| 2  |
        | max_inactive_days| 3  |

  # ========== 學員能力檔案 ==========

  Rule: 後置（回應）- 學員能力檔案應回傳各知識節點的獨立分數

    Example: 查看學員能力檔案取得多維度分析
      When 使用者 "org-admin@school.com" 查看學員 4 的能力分析
      Then 操作成功
      And 回應應包含學員 ID 4 的能力列表
      And 每個能力節點應包含：
        | 欄位   | 說明                                    |
        | label  | 知識節點名稱                            |
        | score  | 0-100 分                                |
        | color  | green（>= 70）/ orange（40-69）/ red（< 40）|

  Rule: 後置（回應）- AI 補強建議應根據學員弱點生成 1 至 3 條針對性任務

    Example: 為學員生成 AI 補強建議成功
      When 使用者 "org-admin@school.com" 為學員 5 請求 AI 補強建議
      Then 操作成功
      And 回應應包含 1 至 3 條建議
      And 每條建議應包含：
        | 欄位            | 說明                         |
        | topic           | 針對的弱點節點名稱           |
        | suggestion      | AI 生成的補強描述（繁體中文）|
        | action_type     | review / quiz / explore      |

    Example: 非機構管理員無法請求 AI 補強建議
      When 使用者 "student1@school.com" 為學員 5 請求 AI 補強建議
      Then 操作失敗，錯誤為「您沒有機構管理員權限」

  # ========== 學員列表 ==========

  Rule: 後置（回應）- 學員列表應包含趨勢指標

    Example: 查看學員列表取得趨勢資訊
      When 使用者 "org-admin@school.com" 查看機構 1 的學員列表
      Then 操作成功
      And 每位學員應包含 trend 欄位
      And trend 計算規則為：
        | 條件                     | trend |
        | 最近平均 > 前次平均 5 分 | up    |
        | 最近平均 < 前次平均 5 分 | down  |
        | 差距在 ±5 分以內         | flat  |
