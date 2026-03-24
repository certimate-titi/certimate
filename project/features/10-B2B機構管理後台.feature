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

  # ========== Redmenta 啟發功能 ==========

  Rule: 後置（回應）- 班級健康 KPI 應回傳四項摘要數值

    # 對應頁面頂部 KPI 卡片列（總學生數 / 活躍率 / 需關注人數 / 班級平均分）

    Example: 機構管理員查看班級健康 KPI
      When 使用者 "admin@school.com" 查看機構 1 的班級健康摘要
      Then 操作成功
      And 回應應包含以下欄位：
        | 欄位         | 說明                                          |
        | total        | 機構授權總學員數                              |
        | active_rate  | 過去 7 天有登入的學員比例（0.0–1.0）          |
        | at_risk_count| 需關注學員人數（平均分 < 60 或趨勢連續下降）  |
        | avg_score    | 全班最近一次測驗的平均分數                    |

  Rule: 後置（回應）- 早期預警應自動偵測並回傳需關注學員清單

    # 觸發條件：平均分低於 60 分，或連續 3 次測驗趨勢下降，或 5 天以上未登入
    # 參考 Redmenta 的 Early Detection 設計，主動浮出問題而非等待教師翻查

    Example: 機構管理員查看需關注學員清單
      When 使用者 "admin@school.com" 查看機構 1 的早期預警清單
      Then 操作成功
      And 回應中每位需關注學員應包含：
        | 欄位             | 說明                                    |
        | student_id       | 學員 ID                                 |
        | name             | 學員姓名                                |
        | avg_score        | 最近測驗平均分數                        |
        | trend            | 近期分數趨勢：up / down / flat          |
        | weakest_topic    | 最弱知識節點名稱                        |
        | weakest_score    | 最弱知識節點分數                        |
        | last_active_days | 距上次登入天數                          |

    Example: 學員平均分低於 60 分應被列入預警清單
      Given 學員 "student2@school.com" 最近三次測驗分數為 45、52、48
      When 使用者 "admin@school.com" 查看機構 1 的早期預警清單
      Then 回應中應包含 "student2@school.com"
      And 該學員的 trend 應為 "flat"

  Rule: 後置（回應）- 個別學員能力檔案應回傳多維度技能分析

    # 對應展開單一學員列時顯示的能力分析列（Redmenta 的 Competency Profiles）
    # 每個知識節點獨立計算分數，而非只有單一整體分數

    Example: 機構管理員查看學員 student1 的能力檔案
      When 使用者 "admin@school.com" 查看學員 4 的能力分析
      Then 操作成功
      And 回應應包含以下結構：
        | 欄位            | 說明                                        |
        | student_id      | 學員 ID                                     |
        | competencies    | 知識節點能力列表（陣列）                    |
      And 每個能力節點應包含：
        | 欄位   | 說明                              |
        | label  | 節點名稱（如：風險管理、EVM 計算） |
        | score  | 0–100 分                          |
        | color  | 綠色（≥70）/ 橘色（40–69）/ 紅色（<40）|

  Rule: 後置（回應）- AI 個人化補強建議應根據學員弱點生成針對性任務清單

    # 對應學員能力檔案展開後的「AI 個人化補強建議」按鈕（Redmenta 的 Personalise 設計）
    # 系統依學員各節點分數，讓 AI 生成具體建議而非通用內容

    Example: 機構管理員為學員 student2 請求 AI 補強建議
      When 使用者 "admin@school.com" 呼叫 POST /students/5/ai-reinforcement
      Then 操作成功
      And 回應應包含 1 至 3 條補強建議
      And 每條建議應包含：
        | 欄位            | 說明                                        |
        | topic           | 針對的弱點節點名稱                          |
        | suggestion      | AI 生成的補強方式描述（繁體中文）           |
        | action_type     | 建議動作類型：review / quiz / explore       |

    Example: 非機構管理員無法呼叫 AI 補強建議 API
      When 使用者 "student1@school.com" 呼叫 POST /students/5/ai-reinforcement
      Then 操作失敗
      And 錯誤訊息應為 "您沒有機構管理員權限"

  Rule: 後置（回應）- 學員列表應包含趨勢指標欄位

    # 前端依 trend 欄位顯示 ↑↓→ 圖示

    Example: 機構管理員查看機構學員列表包含趨勢資訊
      When 使用者 "admin@school.com" 查看機構 1 的學員列表
      Then 操作成功
      And 每位學員資料應包含 trend 欄位（up / down / flat）
      And trend 應依最近 3 次測驗平均分的變化計算：
        | 條件                     | trend  |
        | 最近平均 > 前次平均 5 分 | up     |
        | 最近平均 < 前次平均 5 分 | down   |
        | 差距在 ±5 分以內         | flat   |
