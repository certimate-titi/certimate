Feature: 資源上傳

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | free@example.com   | FREE     |
      | 2        | pro@example.com    | PRO      |
      | 3        | ultra@example.com  | ULTRA    |
    And 系統中有以下資源：
      | 資源 ID | 使用者 ID | 名稱                    | 類型  | 狀態      |
      | 1       | 1        | AWS基礎講義.pdf         | PDF   | COMPLETED |
      | 2       | 2        | 架構設計筆記.md         | MD    | COMPLETED |
      | 3       | 1        | 舊版資料.pdf            | PDF   | FAILED    |
      | 4       | 2        | 電路學手寫公式.png      | IMAGE | COMPLETED |
      | 5       | 3        | 熱力學方程式筆記.jpg    | IMAGE | PROCESSING|

  # ========== 前置條件 ==========

  Rule: 前置（參數）- 上傳檔案類型必須在允許清單內

    Scenario Outline: 上傳不支援的檔案類型失敗
      When 使用者 "pro@example.com" 上傳檔案 "document.<副檔名>"
      Then 操作失敗
      And 錯誤訊息應為 "不支援的檔案格式，請上傳 PDF、Markdown 或圖片檔案"

      Examples:
        | 副檔名 |
        | docx   |
        | xlsx   |
        | mp4    |
        | zip    |

  Rule: 前置（狀態）- 上傳前須勾選合法使用與著作權免責承諾

    Example: 未同意著作權免責聲明上傳失敗
      When 使用者 "pro@example.com" 上傳檔案 "document.pdf"，但未勾選同意「合法著作權與無機密資訊承諾」
      Then 操作失敗
      And 錯誤訊息應為 "您必須確認並同意上傳內容的合法使用權利"

  Rule: 前置（參數）- 檔案大小不得超過訂閱方案的限制

    Example: FREE 方案上傳超過 10MB 的檔案失敗
      When 使用者 "free@example.com" 上傳大小為 12MB 的 PDF 檔案
      Then 操作失敗
      And 錯誤訊息應為 "檔案大小超過 FREE 方案限制（10MB）"

    Example: PRO 方案上傳超過 50MB 的檔案失敗
      When 使用者 "pro@example.com" 上傳大小為 60MB 的 PDF 檔案
      Then 操作失敗
      And 錯誤訊息應為 "檔案大小超過 PRO 方案限制（50MB）"

    Example: PRO 方案上傳未超過限制的檔案成功
      When 使用者 "pro@example.com" 上傳大小為 45MB 的 PDF 檔案
      Then 操作成功

  Rule: 前置（參數）- 手寫數學/工程圖片必須為支援的影像格式

    Scenario Outline: 上傳支援的影像格式成功建立資源
      When 使用者 "pro@example.com" 上傳大小為 3MB 的影像檔案 "手寫筆記.<副檔名>"
      Then 操作成功
      And 新建立的資源類型應為 "IMAGE"
      And 新建立的資源狀態應為 "PENDING"

      Examples:
        | 副檔名 |
        | png    |
        | jpg    |
        | jpeg   |
        | webp   |

    Example: 上傳影像檔案大小超過方案限制失敗
      When 使用者 "free@example.com" 上傳大小為 15MB 的 PNG 影像檔案
      Then 操作失敗
      And 錯誤訊息應為 "檔案大小超過 FREE 方案限制（10MB）"

  Rule: 前置（參數）- YouTube URL 必須為合法格式

    Scenario Outline: 輸入不合法的 YouTube URL 失敗
      When 使用者 "free@example.com" 提交 YouTube URL "<url>"
      Then 操作失敗
      And 錯誤訊息應為 "無效的 YouTube 網址格式"

      Examples:
        | url                      |
        | https://vimeo.com/123456 |
        | not-a-url                |
        | https://youtube.com/     |

    Example: 輸入合法的 YouTube 完整 URL 成功建立資源
      When 使用者 "free@example.com" 提交 YouTube URL "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
      Then 操作成功
      And 系統應建立狀態為 "PENDING" 的新資源記錄

  # ========== 後置條件 ==========

  Rule: 後置（狀態）- 資源上傳後應依序經歷 PENDING → PROCESSING → COMPLETED 或 FAILED 的狀態轉換

    Example: 成功上傳 PDF 後資源初始狀態為 PENDING
      When 使用者 "pro@example.com" 上傳大小為 2MB 的合法 PDF 檔案 "複習筆記.pdf"
      Then 操作成功
      And 新建立的資源狀態應為 "PENDING"

    Example: 解析服務接手後資源狀態轉為 PROCESSING
      Given 資源 1 的狀態為 "PENDING"
      When 後端解析服務開始處理資源 1
      Then 資源 1 的狀態應更新為 "PROCESSING"

    Example: 解析完成後資源狀態轉為 COMPLETED 且心智圖節點生成
      Given 資源 1 的狀態為 "PROCESSING"
      When 後端解析服務成功完成資源 1 的解析
      Then 資源 1 的狀態應更新為 "COMPLETED"
      And 資源 1 應關聯至少一個心智圖知識節點

    Example: 解析失敗後資源狀態轉為 FAILED 且保留失敗原因
      Given 資源 1 的狀態為 "PROCESSING"
      When 後端解析服務處理資源 1 時發生錯誤
      Then 資源 1 的狀態應更新為 "FAILED"
      And 資源 1 應記錄失敗原因訊息

  Rule: 後置（狀態）- IMAGE 類型資源解析完成後應將手寫數學公式轉換為 KaTeX 格式

    Example: 手寫數學公式圖片解析完成後知識節點內容包含 KaTeX 格式的公式
      Given 資源 4 為使用者 "pro@example.com" 的 IMAGE 類型資源，狀態為 "PROCESSING"
      When 後端 Vision OCR 服務成功識別資源 4 的手寫內容
      Then 資源 4 的狀態應更新為 "COMPLETED"
      And 資源 4 關聯的知識節點應包含以下 KaTeX 格式的數學公式：
        | 識別結果（KaTeX）      |
        | V = IR                 |
        | P = \frac{V^2}{R}      |

    Example: 手寫工程圖含多行方程式時全部轉換為 KaTeX 格式並各自對應獨立知識節點
      Given 資源 5 為使用者 "ultra@example.com" 的 IMAGE 類型資源，狀態為 "PROCESSING"
      When 後端 Vision OCR 服務成功識別資源 5 的手寫內容
      Then 資源 5 的狀態應更新為 "COMPLETED"
      And 資源 5 關聯的知識節點應包含以下 KaTeX 格式的數學公式：
        | 識別結果（KaTeX）                                                 |
        | \Delta U = Q - W                                                  |
        | \eta = 1 - \frac{T_{\text{冷}}}{T_{\text{熱}}}                   |

    Example: 無法識別手寫內容時資源狀態轉為 FAILED 並記錄 OCR 失敗原因
      Given 資源 4 為使用者 "pro@example.com" 的 IMAGE 類型資源，狀態為 "PROCESSING"
      When 後端 Vision OCR 服務無法識別資源 4 的手寫內容
      Then 資源 4 的狀態應更新為 "FAILED"
      And 資源 4 應記錄失敗原因訊息 "無法識別圖片中的手寫內容，請嘗試上傳更清晰的圖片"

  Rule: 後置（回應）- 成功上傳後應回傳資源 ID 與初始狀態供前端輪詢

    Example: 上傳完成後回傳資源基本資訊
      When 使用者 "pro@example.com" 上傳大小為 5MB 的合法 PDF 檔案 "AWS_SAA_準備資料.pdf"
      Then 操作成功
      And 回應應包含：
        | 欄位   | 說明                   |
        | 資源ID | 系統配發的唯一識別碼   |
        | 名稱   | AWS_SAA_準備資料.pdf   |
        | 狀態   | PENDING                |

  Rule: 後置（狀態）- 資源解析任務的狀態同步機制 (SSE 或輪詢)

    Example: 前端建立 SSE 連線以即時接收任務狀態更新
      Given 系統已接受文件上傳並回傳 資源ID "doc_123" 與 任務ID "task_123"
      When 前端對 任務ID "task_123" 發起 SSE 或狀態輪詢請求
      Then 系統應於狀態改變時推送事件：
        | 事件名          | 狀態值      | 附加資訊                                |
        | status_update  | PROCESSING | "正在萃取文字內容" 或 "正在生成知識節點" |
      And 任務完成時應推送事件 "COMPLETED" 並自動結束連線
      And 發生錯誤時應推送事件 "FAILED" 包含失敗原因並關閉連線
