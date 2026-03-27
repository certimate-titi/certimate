Feature: 模擬機考

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |
      | 2        | bob@example.com    | PRO      |
    And 系統中有以下測驗：
      | 測驗 ID | 使用者 ID | 狀態        | 總題數 | 考試時長（分鐘） |
      | 1       | 1        | READY       | 10     | 30              |
      | 2       | 2        | READY       | 50     | 90              |
      | 3       | 1        | IN_PROGRESS | 10     | 30              |
      | 4       | 1        | SUBMITTED   | 10     | 30              |
    And 測驗 1 包含以下題目：
      | 題目 ID | 題號 | 題目內容                         | 選項A     | 選項B    | 選項C   | 選項D     |
      | 101     | 1    | AWS S3 的儲存類型何者最便宜？     | Standard  | IA       | Glacier | Express   |
      | 102     | 2    | EC2 定價模式中何者最具彈性？      | On-Demand | Reserved | Spot    | Dedicated |
    And 測驗 3 包含以下題目：
      | 題目 ID | 題號 | 題目內容                         | 選項A     | 選項B    | 選項C   | 選項D     |
      | 301     | 1    | AWS S3 的儲存類型何者最便宜？     | Standard  | IA       | Glacier | Express   |
      | 302     | 2    | EC2 定價模式中何者最具彈性？      | On-Demand | Reserved | Spot    | Dedicated |
    And 測驗 3 包含以下已暫存作答：
      | 題目 ID | 選擇答案 | 已標記複查 |
      | 301     | C        | 否         |
    And 系統中有以下測驗：
      | 測驗 ID | 使用者 ID | 狀態  | 總題數 | 考試時長（分鐘） |
      | 5       | 2        | READY | 5      | 20              |
    And 測驗 5 包含以下數學工程題目：
      | 題目 ID | 題號 | 題型   | 題目內容（含 KaTeX）                                       | 選項A                   | 選項B                  | 選項C                        | 選項D |
      | 201     | 1    | 單選   | 電阻 $R = 10\,\Omega$，電壓 $V = 5\,\text{V}$，電流為何？ | $I = 0.5\,\text{A}$     | $I = 2\,\text{A}$      | $I = 50\,\text{A}$           | $I = 0.1\,\text{A}$ |
      | 202     | 2    | 填空   | 根據歐姆定律 $V = IR$，若 $I = 2\,\text{A}$，$R = 5\,\Omega$，則 $V =$ ___| null | null | null | null |
      | 203     | 3    | 多選   | 下列哪些是熱力學第一定律的正確表述？                       | $\Delta U = Q - W$      | $Q = \Delta U + W$     | $W = Q - \Delta U$           | $\Delta U = Q + W$ |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 只能開始狀態為 READY 的測驗

    Example: 無法重新開始已提交的測驗
      When 使用者 "alice@example.com" 開始測驗 4
      Then 操作失敗
      And 錯誤訊息應為 "測驗已提交，無法重新開始"

  Rule: 前置（狀態）- 只能操作屬於自己的測驗

    Example: 無法開始其他使用者的測驗
      When 使用者 "alice@example.com" 開始測驗 2
      Then 操作失敗
      And 錯誤訊息應為 "無存取此測驗的權限"

  # ========== 後置條件 ==========

  Rule: 後置（狀態）- 開始測驗後狀態更新為 IN_PROGRESS 且倒數計時開始

    Example: 成功開始 READY 狀態的測驗
      When 使用者 "alice@example.com" 開始測驗 1
      Then 操作成功
      And 測驗 1 的狀態應更新為 "IN_PROGRESS"
      And 測驗 1 應記錄開始時間

  @ignore
  Rule: 後置（回應）- AI 教練在開始測驗時提供專屬的打氣訊息

    Example: 開始測驗前 AI 基於使用者狀態動態生成打氣語句
      Given 使用者 "alice@example.com" 準備開始測驗 1
      When 系統載入測驗的初始畫面
      Then 畫面應短暫顯示 AI 教練角色（Certi）的打氣介面
      And AI 教練應提供基於使用者近期學習狀態或連續測驗次數所生成的專屬鼓勵對話

  Rule: 後置（狀態）- 使用者選擇答案後應自動儲存至後端

    Example: 選擇答案後作答記錄被儲存
      Given 使用者 "alice@example.com" 已開始測驗 1
      When 使用者 "alice@example.com" 在題目 101 選擇答案 "C"
      Then 測驗 1 中題目 101 的暫存作答應為 "C"

  Rule: 後置（狀態）- 標記複查後題目應更新複查狀態

    Example: 標記複查後題目複查狀態更新
      Given 使用者 "alice@example.com" 已開始測驗 1
      When 使用者 "alice@example.com" 將題目 102 標記為待複查
      Then 題目 102 的標記複查狀態應為 "已標記"

  @ignore
  Rule: 後置（狀態）- 倒數計時器在剩餘 5 分鐘時觸發紅色警示樣式

    Example: 剩餘時間低於 5 分鐘時計時器顯示樣式切換為紅色警示
      Given 使用者 "alice@example.com" 已開始測驗 1，剩餘時間為 6 分鐘
      When 系統時間推進使剩餘時間變為 4 分 59 秒
      Then 計時器的顯示樣式應切換為 "紅色警示"

  Rule: 後置（狀態）- 計時結束後測驗提交並更新狀態為 SUBMITTED

    Example: 提交測驗後狀態更新
      Given 使用者 "alice@example.com" 已開始測驗 1
      When 使用者 "alice@example.com" 提交測驗 1
      Then 操作成功
      And 測驗 1 的狀態應更新為 "SUBMITTED"

  Rule: 後置（回應）- 繼續進行中的測驗時應恢復已暫存的作答記錄

    Example: 重新進入進行中的測驗時恢復暫存狀態
      When 使用者 "alice@example.com" 繼續進行測驗 3
      Then 操作成功
      And 題目 301 的已選答案應為 "C"

  @ignore
  Rule: 後置（狀態）- 使用者嘗試離開頁面時應觸發 beforeunload 警告

    Example: 測驗中關閉分頁前出現確認提示
      Given 使用者 "alice@example.com" 已開始測驗 1
      When 使用者 "alice@example.com" 嘗試關閉測驗頁面
      Then 系統應觸發 beforeunload 警告訊息
      And 警告訊息應為 "確定要離開測驗嗎？您的進度已暫存"

  @ignore
  Rule: 後置（回應）- 含 KaTeX 數學公式的題目應以渲染後的數學符號呈現

    Example: 顯示含 KaTeX 公式的單選題時題目區與選項區均完成數學符號渲染
      Given 使用者 "bob@example.com" 已開始測驗 5
      When 使用者 "bob@example.com" 瀏覽題目 201
      Then 題目顯示區應渲染以下 KaTeX 內容：
        | 位置   | KaTeX 原始碼                                               | 渲染結果說明                 |
        | 題目   | R = 10\,\Omega，V = 5\,\text{V}                            | 顯示歐姆符號與伏特單位       |
        | 選項 A | I = 0.5\,\text{A}                                          | 顯示安培單位                 |
        | 選項 B | I = 2\,\text{A}                                            | 顯示安培單位                 |

    Example: 顯示含 KaTeX 公式的多選題時所有選項均完成渲染且支援多選勾選狀態
      Given 使用者 "bob@example.com" 已開始測驗 5
      When 使用者 "bob@example.com" 瀏覽題目 203
      Then 題目顯示區應以多選核取方塊呈現每個選項
      And 每個選項應正確渲染 KaTeX 公式符號

  Rule: 後置（狀態）- 填空題的作答應儲存使用者輸入的文字至後端

    Example: 填空題輸入數學答案後作答記錄被儲存
      Given 使用者 "bob@example.com" 已開始測驗 5
      When 使用者 "bob@example.com" 在題目 202 的填空欄輸入 "10"
      Then 測驗 5 中題目 202 的暫存作答應為 "10"

    @ignore
    Example: 填空題未作答時題號導覽網格顯示為灰色未答狀態
      Given 使用者 "bob@example.com" 已開始測驗 5
      When 使用者 "bob@example.com" 瀏覽題目 202 但未輸入任何內容
      Then 題目 202 在題號導覽網格的狀態應為 "未作答"
