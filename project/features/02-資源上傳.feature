@command
Feature: 資源上傳與隱性版權約定

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 訂閱方案      |
      | 1        | free@example.com     | FREE          |
      | 2        | pro@example.com      | PRO_199       |
      | 3        | proplus@example.com  | PRO_PLUS_399  |
      | 4        | ultra@example.com    | ULTRA_1599    |
    And 使用者 "free@example.com" 備考科目為 "AWS SAA"（科目 ID: 1）
    And 使用者 "pro@example.com" 備考科目為 "AWS SAA"（科目 ID: 1）
    And 使用者 "proplus@example.com" 備考科目為 "AWS SAA"（科目 ID: 1）
    And 使用者 "ultra@example.com" 備考科目為 "AWS SAA"（科目 ID: 1）

  # ========== 前置條件：檔案格式 ==========

  Rule: 前置（參數）- 上傳檔案類型必須在允許清單內

    Scenario Outline: 上傳不支援的 <副檔名> 檔案失敗
      When 使用者 "pro@example.com" 上傳檔案 "document.<副檔名>"，科目為 1
      Then 操作失敗，錯誤為「不支援的檔案格式，請上傳 PDF、Markdown 或通用圖片檔案」

      Examples:
        | 副檔名 |
        | docx   |
        | mp4    |
        | exe    |

  # ========== 前置條件：檔案大小 ==========

  Rule: 前置（參數）- 檔案大小不得超過訂閱方案限制

    Example: FREE 方案上傳超過 10MB 的檔案失敗
      When 使用者 "free@example.com" 上傳大小為 12MB 的 PDF 檔案 "大型講義.pdf"，科目為 1
      Then 操作失敗，錯誤為「檔案大小超過 FREE 方案限制（10MB）」

    Example: PRO 方案上傳 95MB 檔案成功
      When 使用者 "pro@example.com" 上傳大小為 95MB 的 PDF 檔案 "進階教材.pdf"，科目為 1
      Then 操作成功

    Example: PRO_PLUS 方案上傳 95MB 檔案成功
      When 使用者 "proplus@example.com" 上傳大小為 95MB 的 PDF 檔案 "專業教材.pdf"，科目為 1
      Then 操作成功

    Example: PRO 方案上傳超過 100MB 的檔案失敗
      When 使用者 "pro@example.com" 上傳大小為 105MB 的 PDF 檔案 "超大教材.pdf"，科目為 1
      Then 操作失敗，錯誤為「檔案大小超過 PRO_199 方案限制（100MB）」

    Example: ULTRA 方案上傳 300MB 檔案成功
      When 使用者 "ultra@example.com" 上傳大小為 300MB 的 PDF 檔案 "教科書合輯.pdf"，科目為 1
      Then 操作成功

  # ========== 前置條件：Vision OCR 權限 ==========

  Rule: 前置（狀態）- 影像檔案（Vision OCR）僅 PRO_PLUS 以上方案可上傳

    Example: PRO 用戶上傳影像檔案失敗並提示升級
      When 使用者 "pro@example.com" 上傳影像檔案 "工數手寫筆記.png"，大小為 3MB，科目為 1
      Then 操作失敗，錯誤為「手寫圖片辨識（Vision OCR）需升級至 PRO_PLUS 方案」

    Example: PRO_PLUS 用戶上傳影像檔案成功
      When 使用者 "proplus@example.com" 上傳影像檔案 "手寫推導.png"，大小為 3MB，科目為 1
      Then 操作成功
      And 新建立的資源狀態應為 "PENDING"
      And 預定使用的解析引擎應為 "vision_ocr"

  # ========== 前置條件：必要參數 ==========

  Rule: 前置（參數）- 上傳必須提供檔案與科目 ID

    Scenario Outline: 缺少 <缺少參數> 時上傳失敗
      When 使用者 "free@example.com" 上傳檔案 <檔案>，科目為 <科目ID>
      Then 操作失敗，錯誤為「必要參數未提供」

      Examples:
        | 缺少參數 | 檔案         | 科目ID |
        | 檔案     |              | 1      |
        | 科目 ID  | test.pdf     |        |

  # ========== 隱性版權約定 ==========

  Rule: 後置（狀態）- 點擊上傳即視為同意免責條款並自動記錄

    Example: 使用者上傳檔案後系統自動記錄隱性同意
      When 使用者 "free@example.com" 上傳 PDF 檔案 "筆記.pdf"，大小為 5MB，科目為 1
      Then 操作成功
      And 新建立的資源應標記 implicit_consent 為 true

  # ========== YouTube URL ==========

  Rule: 後置（狀態）- YouTube URL 各方案皆可提交且無時長限制

    Example: FREE 用戶提交 YouTube URL 成功
      When 使用者 "free@example.com" 提交 YouTube URL "https://www.youtube.com/watch?v=abc123"，科目為 1
      Then 操作成功
      And 新建立的資源類型應為 "youtube"
      And 新建立的資源狀態應為 "PENDING"

    Example: PRO 用戶提交長時間 YouTube 影片成功
      When 使用者 "pro@example.com" 提交 YouTube URL "https://www.youtube.com/watch?v=10hour_course"，科目為 1
      Then 操作成功
      And 預定使用的解析引擎應為 "gemini_flash"

  Rule: 前置（參數）- YouTube URL 格式必須有效

    Example: 提交無效的 YouTube URL 失敗
      When 使用者 "free@example.com" 提交 YouTube URL "https://not-youtube.com/video"，科目為 1
      Then 操作失敗，錯誤為「無效的 YouTube URL」
