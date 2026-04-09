@command
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

  # ========== EDU 學生方案與機構人數上限 ==========

  Rule: 前置（狀態）- ULTRA 方案含 30 名 EDU 學生，超過需額外付費

    Example: 匯入第 31 名學生時提示需額外付費
      Given 機構 1 目前已有 30 名 EDU 學生
      When 使用者 "org-admin@school.com" 上傳包含 1 名新學生的 CSV 進行學員匯入
      Then 操作失敗，錯誤為「已達免費學生上限（30 名），每增加一名學生需額外 NT$30/月，請確認後再匯入」

    Example: 確認加購後匯入第 31 名學生成功
      Given 機構 1 目前已有 30 名 EDU 學生
      When 使用者 "org-admin@school.com" 上傳包含 1 名新學生的 CSV 進行學員匯入，並確認加購
      Then 操作成功
      And 系統應建立 1 個新學員帳號，方案為 "EDU"
      And 機構 1 的每月附加費用應為 NT$30

  Rule: 後置（狀態）- 匯入學生後帳號自動設定為 EDU 方案與 student 角色

    Example: CSV 匯入學生自動指派 EDU 方案
      When 使用者 "org-admin@school.com" 上傳以下合法 CSV 進行學員匯入：
        | 姓名   | 電子郵件          | 群組             |
        | 新同學 | new@example.com   | AWS 雲端基礎班 A |
      Then 操作成功
      And 使用者 "new@example.com" 的訂閱方案應為 "EDU"
      And 使用者 "new@example.com" 的角色應為 "student"
      And 使用者 "new@example.com" 的每日 AI 對話限額應為 5
      And 使用者 "new@example.com" 不可上傳資源
      And 使用者 "new@example.com" 不可自主建立測驗

  # ========== DPA 資料處理合約 ==========

  Rule: 前置（狀態）- 機構管理員首次匯入學生前須簽署資料處理合約（DPA）

    Example: 未簽署 DPA 即匯入學生失敗
      Given 使用者 "org-admin@school.com" 尚未簽署機構資料處理合約
      When 使用者 "org-admin@school.com" 上傳合法 CSV 進行學員匯入，並已勾選同意「學員資料處理條款」
      Then 操作失敗，錯誤為「請先簽署機構資料處理合約（DPA）後才可匯入學生資料」

    Example: 已簽署 DPA 後匯入學生成功
      Given 使用者 "org-admin@school.com" 已簽署機構資料處理合約
      When 使用者 "org-admin@school.com" 上傳以下合法 CSV 進行學員匯入：
        | 姓名   | 電子郵件          | 群組             |
        | 王小明 | wang@example.com  | PMP 衝刺班 B     |
      Then 操作成功

  Rule: 後置（回應）- 機構管理員可查看已簽署的 DPA 記錄

    Example: 查看 DPA 簽署記錄
      Given 使用者 "org-admin@school.com" 已於 2026-03-15 簽署機構資料處理合約
      When 使用者 "org-admin@school.com" 查看機構 1 的 DPA 簽署記錄
      Then 操作成功
      And 回應應包含：
        | 欄位        | 值              |
        | signed_at   | 2026-03-15      |
        | signed_by   | org-admin@school.com |
        | version     | 1.0             |

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

  # ========== 空狀態 ==========

  Rule: 前置（狀態）- 機構尚無學員群組時應顯示空狀態引導

    Example: 機構無學員群組時查看學員列表返回空狀態
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                     | 訂閱方案   | 角色      |
        | 7        | new-admin@school.com      | ULTRA_1599 | org_admin |
      And 系統中有以下機構：
        | 機構 ID | 名稱         | 管理員 ID |
        | 2       | 新建補習班   | 7         |
      When 使用者 "new-admin@school.com" 查看機構 2 的學員列表
      Then 操作成功
      And 回應中學員列表應為空
      And 回應應包含空狀態提示「尚未匯入任何學員，請先透過 CSV 匯入學生名單」

    Example: 機構有群組但群組內無學員時顯示空狀態
      When 使用者 "org-admin@school.com" 查看群組 2 的學員列表
      Then 操作成功
      And 回應中學員列表應為空
      And 回應應包含空狀態提示「此群組尚無學員，請透過 CSV 匯入或手動新增」

    Example: 機構管理員首次進入管理後台時顯示初始化引導
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                     | 訂閱方案   | 角色      |
        | 8        | fresh-admin@school.com    | ULTRA_1599 | org_admin |
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

    Example: AI 補強建議應根據學員能力弱項提供分級建議
      Given 學員 "student2@school.com" 的能力分析為：
        | 知識節點     | 分數 |
        | 雲端運算基礎 | 62   |
        | 網路安全     | 38   |
        | IAM 身分管理 | 25   |
        | 資料庫管理   | 70   |
        | 成本最佳化   | 45   |
      When 使用者 "org-admin@school.com" 為學員 5 請求 AI 補強建議
      Then 操作成功
      And 回應應包含至少 3 條建議
      And 建議應優先針對分數最低的能力（IAM 身分管理、網路安全）
      And 回應應包含一條 action_type 為 "plan" 的整體建議

  # ========== 學員詳情報告 ==========

  Rule: 後置（回應）- 學員詳情報告應回傳考試統計與強弱項分析

    Example: 查看學員詳情報告取得考試摘要與強弱項
      Given 學員 "student1@school.com" 已完成以下考試：
        | 考試 ID | 分數 | 總題數 | 正確數 | 繳交時間                 |
        | 1       | 88   | 20     | 18     | 2026-04-03T14:30:00+08:00 |
        | 2       | 78   | 20     | 16     | 2026-03-28T10:15:00+08:00 |
        | 3       | 70   | 20     | 14     | 2026-03-20T16:45:00+08:00 |
      When 使用者 "org-admin@school.com" 查看學員 4 的詳情報告
      Then 操作成功
      And 回應應包含：
        | 欄位          | 值               |
        | student_id    | 4                |
        | exam_count    | 3                |
        | average_score | 79               |
      And 回應應包含 strengths 列表（分數 >= 70 的能力節點）
      And 回應應包含 weaknesses 列表（分數 < 50 的能力節點）

    Example: 非機構管理員無法查看學員詳情報告
      When 使用者 "student1@school.com" 查看學員 5 的詳情報告
      Then 操作失敗，錯誤為「您沒有機構管理員權限」

    Example: 查看不存在的學員詳情報告回傳錯誤
      When 使用者 "org-admin@school.com" 查看學員 999 的詳情報告
      Then 操作失敗，錯誤為「找不到此學生」

  # ========== 考試歷程與錯題詳情 ==========

  Rule: 後置（回應）- 學員詳情報告中的考試歷程應包含每次考試的錯題詳情

    Example: 考試歷程包含錯題的題號、內容、作答與解析
      Given 學員 "student1@school.com" 已完成考試 1（分數 88，共 20 題）
      And 考試 1 中學員答錯以下題目：
        | 題號 | 題目內容                                             | 學生作答 | 正確答案 | 難度   | 解析                                                         |
        | 7    | 在 AWS 中，下列哪個服務負責管理使用者身分與存取權限？ | C        | B        | medium | IAM 是 AWS 負責管理使用者、群組及其存取權限的核心服務         |
        | 15   | VPC 中的 NAT Gateway 主要功能為何？                  | A        | D        | hard   | NAT Gateway 允許私有子網路中的資源連線到網際網路，但不允許外部主動連入 |
      When 使用者 "org-admin@school.com" 查看學員 4 的詳情報告
      Then 操作成功
      And 回應中 exam_history 應包含 1 筆考試紀錄
      And 該考試紀錄的 wrong_answers 應包含 2 筆錯題
      And 每筆錯題應包含：
        | 欄位            | 說明                 |
        | question_number | 題號                 |
        | content         | 題目內容（前 120 字）|
        | student_answer  | 學生作答選項         |
        | correct_answer  | 正確答案選項         |
        | explanation     | 解析說明             |
        | difficulty      | easy / medium / hard |

    Example: 無考試記錄的學員報告中考試歷程為空陣列
      Given 學員 "student2@school.com" 尚未完成任何考試
      When 使用者 "org-admin@school.com" 查看學員 5 的詳情報告
      Then 操作成功
      And 回應中 exam_count 應為 0
      And 回應中 exam_history 應為空陣列

  # ========== 指派補考（個人化補救試卷） ==========

  Rule: 命令（寫入）- 機構管理員可為學員指派個人化補考，按能力比例分配題數

    Example: 指派補考設定各能力比例成功
      When 使用者 "org-admin@school.com" 為學員 4 指派補考，設定如下：
        | 總題數 | 20 |
      And 各能力比例設定為：
        | 能力節點     | 比例 |
        | 雲端運算基礎 | 10%  |
        | 網路安全     | 20%  |
        | IAM 身分管理 | 35%  |
        | 資料庫管理   | 5%   |
        | 成本最佳化   | 30%  |
      Then 操作成功
      And 系統應生成包含 20 題的補救試卷
      And 試卷中各能力的題數分配應為：
        | 能力節點     | 題數 |
        | 雲端運算基礎 | 2    |
        | 網路安全     | 4    |
        | IAM 身分管理 | 7    |
        | 資料庫管理   | 1    |
        | 成本最佳化   | 6    |
      And 系統應自動將補救試卷指派給學員 4

    Example: 各能力比例總和不等於 100% 時指派失敗
      When 使用者 "org-admin@school.com" 為學員 4 指派補考，設定如下：
        | 總題數 | 20 |
      And 各能力比例設定為：
        | 能力節點     | 比例 |
        | 雲端運算基礎 | 10%  |
        | 網路安全     | 20%  |
        | IAM 身分管理 | 35%  |
      Then 操作失敗，錯誤為「各能力比例總和必須等於 100%」

    Example: 支援不同總題數選項
      When 使用者 "org-admin@school.com" 為學員 4 指派補考，設定如下：
        | 總題數 | 50 |
      And 各能力比例設定為：
        | 能力節點     | 比例 |
        | 雲端運算基礎 | 20%  |
        | 網路安全     | 20%  |
        | IAM 身分管理 | 20%  |
        | 資料庫管理   | 20%  |
        | 成本最佳化   | 20%  |
      Then 操作成功
      And 系統應生成包含 50 題的補救試卷
      And 各能力應各分配 10 題

    Example: 非機構管理員無法指派補考
      When 使用者 "student1@school.com" 為學員 5 指派補考，設定如下：
        | 總題數 | 20 |
      And 各能力比例設定為：
        | 能力節點     | 比例  |
        | 雲端運算基礎 | 100%  |
      Then 操作失敗，錯誤為「您沒有機構管理員權限」

  Rule: 後置（回應）- 補考預設比例應依學員弱項自動反向分配

    Example: 系統自動計算補考預設比例
      Given 學員 "student1@school.com" 的能力分析為：
        | 知識節點     | 分數 |
        | 雲端運算基礎 | 85   |
        | 網路安全     | 72   |
        | IAM 身分管理 | 58   |
        | 資料庫管理   | 90   |
        | 成本最佳化   | 65   |
      When 使用者 "org-admin@school.com" 查看學員 4 的補考預設比例
      Then 操作成功
      And 弱項能力（分數較低）應獲得較高的預設比例
      And 各能力的預設比例總和應等於 100%

  # ========== 學員複習排程 ==========

  Rule: 後置（回應）- 機構管理員可查看學員的艾賓浩斯複習排程

    Example: 查看學員複習排程取得未來複習日程
      When 使用者 "org-admin@school.com" 查看學員 4 的複習排程
      Then 操作成功
      And 回應應包含學員 ID 4 的複習排程列表
      And 每筆排程應包含：
        | 欄位           | 說明                     |
        | knowledge_node | 知識節點名稱             |
        | scheduled_date | 預定複習日期             |
        | interval_days  | 距上次複習天數           |
        | status         | pending / completed      |

    Example: 非機構管理員無法查看學員複習排程
      When 使用者 "student1@school.com" 查看學員 5 的複習排程
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

  # ========== 學員搜尋與過濾 ==========

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

  # ========== 班級弱點針對練習卷 ==========

  Rule: 後置（狀態）- 機構管理員可一鍵生成班級弱點加強練習卷

    Example: 為群組生成弱點針對練習卷成功
      Given 群組 1 的班級弱點分析顯示 "IAM 身分管理" 掌握率最低（35%）
      When 使用者 "org-admin@school.com" 為群組 1 生成弱點針對練習卷，題數為 20
      Then 操作成功
      And 練習卷應包含 20 題
      And 練習卷中至少 60% 的題目應來自弱點知識節點
      And 系統應自動將練習卷派發給群組 1 所有學員

    Example: 群組無考試數據時無法生成弱點練習卷
      When 使用者 "org-admin@school.com" 為群組 2 生成弱點針對練習卷，題數為 20
      Then 操作失敗，錯誤為「此群組尚無足夠的考試數據，請先派發考卷」

  # ========== 學員與群組批量管理 ==========

  Rule: 命令（寫入）- 機構管理員可刪除群組

    Example: 刪除空群組
      When 使用者 "org-admin@school.com" 刪除機構 1 的群組 "PMP 衝刺班 B"
      Then 操作成功
      And 機構 1 不再包含群組 "PMP 衝刺班 B"

    Example: 刪除含成員的群組會同時解除學生的群組歸屬
      When 使用者 "org-admin@school.com" 刪除機構 1 的群組 "AWS 雲端基礎班 A"
      Then 操作成功
      And 機構 1 不再包含群組 "AWS 雲端基礎班 A"
      And 使用者 "student1@school.com" 仍存在於機構 1 中
      And 使用者 "student2@school.com" 仍存在於機構 1 中

    Example: 非機構管理員無法刪除群組
      When 使用者 "student1@school.com" 刪除機構 1 的群組 "PMP 衝刺班 B"
      Then 操作失敗，錯誤為「您沒有機構管理員權限」

  Rule: 命令（寫入）- 機構管理員可批量移除學生

    Example: 勾選多位學生後批量移除
      When 使用者 "org-admin@school.com" 批量移除機構 1 的以下學生：
        | Email               |
        | student1@school.com |
        | student2@school.com |
      Then 操作成功
      And 機構 1 的學生數量應為 0

    Example: 非機構管理員無法批量移除學生
      When 使用者 "student1@school.com" 批量移除機構 1 的以下學生：
        | Email               |
        | student2@school.com |
      Then 操作失敗，錯誤為「您沒有機構管理員權限」

  Rule: 命令（寫入）- 機構管理員可移除單一學生

    Example: 從操作選單移除學生
      When 使用者 "org-admin@school.com" 移除機構 1 的學生 "student1@school.com"
      Then 操作成功
      And 使用者 "student1@school.com" 不再屬於機構 1

    Example: 移除不存在的學生回傳錯誤
      When 使用者 "org-admin@school.com" 移除機構 1 的學生 "notexist@school.com"
      Then 操作失敗，錯誤為「找不到該學生」

  # ========== 未實作功能 Placeholder ==========

  Rule: 後置（回應）- 匯入學生名單按鈕顯示未實作提示

    Example: 點擊匯入學生名單按鈕顯示即將推出提示
      When 使用者 "org-admin@school.com" 在機構管理後台點擊「匯入學生名單」按鈕
      Then 系統應顯示提示訊息「此功能即將推出，敬請期待」

  Rule: 後置（回應）- 快速操作卡片點擊顯示未實作提示

    Example: 點擊快速操作卡片顯示即將推出提示
      When 使用者 "org-admin@school.com" 在機構管理後台點擊快速操作卡片
      Then 系統應顯示提示訊息「此功能即將推出，敬請期待」

  Rule: 後置（回應）- 匯出詳細報告按鈕顯示未實作提示

    Example: 點擊匯出詳細報告按鈕顯示即將推出提示
      When 使用者 "org-admin@school.com" 在班級分析頁點擊「匯出詳細報告」按鈕
      Then 系統應顯示提示訊息「此功能即將推出，敬請期待」
