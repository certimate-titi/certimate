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
      Then 操作失敗，錯誤為「不支援的檔案格式」

      Examples:
        | 副檔名 |
        | exe    |
        | bat    |
        | sh     |

    Scenario Outline: 上傳支援的 <副檔名> 檔案成功
      When 使用者 "pro@example.com" 上傳檔案 "document.<副檔名>"，科目為 1
      Then 操作成功

      Examples:
        | 副檔名 |
        | docx   |
        | pptx   |
        | xlsx   |

  # ========== 前置條件：檔案大小 ==========

  Rule: 前置（參數）- 檔案大小不得超過訂閱方案限制

    Example: FREE 方案上傳超過 10MB 的檔案失敗
      When 使用者 "free@example.com" 上傳大小為 12MB 的 PDF 檔案 "大型講義.pdf"，科目為 1
      Then 操作失敗，錯誤為「檔案大小超過 FREE 方案限制（10MB）」

    Example: PRO 方案上傳 40MB PDF 檔案成功
      When 使用者 "pro@example.com" 上傳大小為 40MB 的 PDF 檔案 "進階教材.pdf"，科目為 1
      Then 操作成功

    Example: PRO_PLUS 方案上傳 40MB PDF 檔案成功
      When 使用者 "proplus@example.com" 上傳大小為 40MB 的 PDF 檔案 "專業教材.pdf"，科目為 1
      Then 操作成功

    Example: PRO 方案上傳超過 100MB 的檔案失敗
      When 使用者 "pro@example.com" 上傳大小為 105MB 的 PDF 檔案 "超大教材.pdf"，科目為 1
      Then 操作失敗，錯誤為「檔案大小超過 PRO_199 方案限制（100MB）」

    Example: PDF 檔案超過 50MB 類型限制失敗
      When 使用者 "ultra@example.com" 上傳大小為 55MB 的 PDF 檔案 "超大教材.pdf"，科目為 1
      Then 操作失敗，錯誤為「檔案大小超過」

    Example: ULTRA 方案上傳 45MB PDF 檔案成功
      When 使用者 "ultra@example.com" 上傳大小為 45MB 的 PDF 檔案 "教科書合輯.pdf"，科目為 1
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

  # ========== 分片上傳（ULTRA 大檔案支援）==========

  Rule: 前置（參數）- 超過 100MB 的檔案必須使用分片上傳

    Example: ULTRA 用戶上傳 300MB 檔案時系統啟動分片上傳流程
      When 使用者 "ultra@example.com" 初始化分片上傳，檔案名稱為 "大型教科書.pdf"，大小為 300MB，科目為 1
      Then 操作成功
      And 回應應包含：
        | 欄位        | 說明                           |
        | upload_id   | 分片上傳任務 ID                |
        | chunk_size  | 每片建議大小（5MB）            |
        | total_chunks| 預計分片數                     |

  Rule: 後置（狀態）- 分片上傳支援斷點續傳

    Example: 上傳中斷後可從斷點續傳
      Given 使用者 "ultra@example.com" 已初始化分片上傳任務，總共 60 片
      And 已成功上傳前 30 片
      When 使用者 "ultra@example.com" 查詢分片上傳進度
      Then 操作成功
      And 回應應包含：
        | 欄位              | 值  |
        | uploaded_chunks   | 30  |
        | total_chunks      | 60  |
        | status            | in_progress |
      And 使用者可從第 31 片繼續上傳

    Example: 所有分片上傳完成後合併檔案
      Given 使用者 "ultra@example.com" 已上傳所有 60 片
      When 使用者 "ultra@example.com" 完成分片上傳合併
      Then 操作成功
      And 新建立的資源狀態應為 "PENDING"
      And 資源檔案大小應為 300MB

  Rule: 前置（狀態）- 非 ULTRA 方案不可使用分片上傳

    Example: PRO 用戶嘗試初始化分片上傳失敗
      When 使用者 "pro@example.com" 初始化分片上傳，檔案名稱為 "大型檔案.pdf"，大小為 200MB，科目為 1
      Then 操作失敗，錯誤為「檔案大小超過 PRO_199 方案限制（100MB）」

  # ========== YouTube URL ==========

  Rule: 前置（參數）- YouTube URL 格式必須有效

    Example: 提交無效的 YouTube URL 失敗
      When 使用者 "free@example.com" 提交 YouTube URL "https://not-youtube.com/video"，科目為 1
      Then 操作失敗，錯誤為「無效的 YouTube URL」

  # ========== 資源分塊查詢（知識庫 accordion 展開）==========

  Rule: 後置（查詢）- 使用者可查詢自己資源的分塊內容

    Example: 查詢自己上傳的資源分塊成功
      Given 使用者 "pro@example.com" 已上傳資源 "我的講義.pdf"（科目 ID: 1）且有 3 個分塊
      When 使用者 "pro@example.com" 查詢資源分塊
      Then 操作成功
      And 回應應包含 3 個分塊

  Rule: 後置（查詢）- Seed 資源的分塊查詢依科目歸屬檢查

    Example: 查詢 seed 資源分塊（有該科目）成功
      Given 系統中有 seed 資源 "考古題庫"（科目 ID: 1）且有 2 個分塊
      When 使用者 "pro@example.com" 查詢 seed 資源分塊
      Then 操作成功
      And 回應應包含 2 個分塊

    Example: 查詢 seed 資源分塊（無該科目）被拒
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                | 訂閱方案 |
        | 5        | other@example.com    | PRO_199  |
      And 系統中有 seed 資源 "其他考古題"（科目 ID: 1）且有 2 個分塊
      When 使用者 "other@example.com" 查詢 seed 資源分塊
      Then 操作失敗，錯誤為「無權存取此資源」

  Rule: 後置（查詢）- 不可查詢他人上傳的資源分塊

    Example: 查詢他人的資源分塊被拒
      Given 使用者 "pro@example.com" 已上傳資源 "他的講義.pdf"（科目 ID: 1）且有 2 個分塊
      When 使用者 "free@example.com" 查詢該資源的分塊
      Then 操作失敗，錯誤為「無權存取此資源」

    Example: 查詢不存在的資源分塊回傳 404
      When 使用者 "pro@example.com" 查詢不存在的資源分塊
      Then 操作失敗，錯誤為「資源不存在」

  # ========== 資源詳情查詢與處理觸發 ==========
  @added-by:cto

  Rule: 後置（查詢）- 使用者可查詢自己資源的詳情

    Example: 查詢自己資源詳情成功
      Given 使用者 "pro@example.com" 已上傳資源 "我的講義.pdf"（科目 ID: 1）且有 1 個分塊
      When 使用者 "pro@example.com" 查詢資源詳情
      Then 操作成功
      And 回應欄位 "filename" 應為 "我的講義.pdf"

    Example: 查詢他人資源詳情應回傳 404
      Given 使用者 "pro@example.com" 已上傳資源 "他的講義.pdf"（科目 ID: 1）且有 1 個分塊
      When 使用者 "free@example.com" 查詢該資源詳情
      Then 操作失敗，錯誤為「資源不存在」

  Rule: 後置（狀態）- 使用者可觸發資源處理流程

    Example: 觸發自己資源的處理流程
      Given 使用者 "pro@example.com" 已上傳資源 "待處理.pdf"（科目 ID: 1）且有 1 個分塊
      When 使用者 "pro@example.com" 觸發資源處理
      Then 操作成功

    Example: 觸發不存在的資源處理應回傳 404
      When 使用者 "pro@example.com" 觸發不存在資源的處理
      Then 操作失敗，錯誤為「資源不存在」

  # ========== 分片上傳單片（ULTRA 實際上傳） ==========
  @added-by:cto

  Rule: 前置（行為）- 分片上傳支援單片上傳 API

    Example: ULTRA 使用者上傳第 0 片
      Given 使用者 "ultra@example.com" 已初始化分片上傳任務，總共 60 片
      When 使用者 "ultra@example.com" 上傳第 0 片（大小為 1024 bytes）
      Then 操作成功

  # ─────────────────────────────────────────────
  # PRD-033：雲端環境 GCS 儲存與 RLS 隔離
  # ─────────────────────────────────────────────
  @prd-033 @infra-heavy @skip
  Rule: 雲端 GCS 儲存 key 需使用 uploads/ 前綴

    # 備註：後端已實作（app/api/resource.py:433+），但測試需 mock GCS client；
    # 暫標 @skip，等建立 GCS mock infrastructure 再啟用。
    Example: 上傳檔案至 GCS 使用統一前綴
      Given 環境變數 STORAGE_BACKEND=gcs, GCS_BUCKET=certimate-titi-data
      When 使用者 "cloud@example.com" 上傳 PDF "sample.pdf"
      Then GCS 物件 key 應為 "uploads/{user_id}/{resource_id}/sample.pdf"
      And resources.file_path 應記錄完整 GCS key

  @prd-033 @infra-heavy @skip
  Rule: 背景解析任務必須重新套用 RLS tenant_id

    # 備註：後端已實作（app/api/resource.py:471,483 呼叫 set_rls_tenant）；
    # 測試需 monkey-patch spy，暫標 @skip。
    Example: BackgroundTasks 新 Session 不繼承連線池汙染的 GUC
      Given 使用者 "cloud@example.com" 觸發資源上傳
      When _process_resource_background 建立新的 _SessionLocal
      Then 背景任務第一步應呼叫 set_rls_tenant(db, tenant_id) 寫入正確 GUC
      And 背景任務查詢 resources 不應因前一個連線的空字串 GUC 失敗

  @added-by:cto @infra-heavy @skip
  Rule: ResourceChunk 建立時必須明確設定 tenant_id（RLS 防護）

    # 備註：後端已實作（DocumentProcessingService 建 chunk 時帶 tenant_id）；
    # 測試需 mock Voyage embedding + Gemini LLM 才能跑完 pipeline，暫標 @skip。
    Example: 背景處理產出的 chunks 必須繼承 Resource.tenant_id
      Given 使用者 "free@example.com" 成功上傳 PDF "notes.pdf"，科目為 1
      When 背景任務 DocumentProcessingService.process_resource 產出 chunks
      Then 每個 ResourceChunk 的 tenant_id 應等於 Resource.tenant_id
      And INSERT resource_chunks 不應因 tenant_id NULL 違反 RLS policy

  @added-by:cto
  Rule: 上傳時同步預檢 PDF（可解析性 + 版權關鍵字）

    Example: 上傳損毀 PDF 應立即回傳 400
      When 使用者 "free@example.com" 上傳損毀的 PDF 檔案「corrupted.pdf」
      Then 操作失敗狀態碼為 400
      And 錯誤訊息應包含「PDF 檔案損毀或無法解析」
      And 不應建立 Resource 紀錄

    Example: 上傳含版權關鍵字 PDF 應立即回傳 400
      When 使用者 "free@example.com" 上傳前兩頁含「版權所有」的 PDF
      Then 操作失敗狀態碼為 400
      And 錯誤訊息應包含「版權限制關鍵字」
      And 不應建立 Resource 紀錄

  @added-by:cto
  Rule: 資源列表須回傳 error_message 供前端顯示具體失敗原因

    Example: FAILED 資源的列表回應包含 error_message
      Given 使用者 "free@example.com" 有一筆 status=FAILED 的資源，error_message 為「版權限制關鍵字」
      When 使用者 "free@example.com" 查詢資源列表
      Then 操作成功
      And 該筆資源的 error_message 欄位應為「版權限制關鍵字」

  @added-by:cto
  Rule: 背景處理失敗時，error_message 須分類標註失敗階段

    失敗原因須以中括號分類前綴，便於用戶快速判斷問題根源：
    - 【版權限制】：觸發版權關鍵字
    - 【萃取失敗】：媒體層讀取失敗（PDF/DOCX/YouTube 解不出文字，含純圖片 PDF）
    - 【轉檔失敗】：文字已擷取但無法轉為 Markdown（例：內容過短、結構無法解析）
    - 【向量化失敗】：Embedding 階段失敗
    - 【系統配額】：Voyage/LLM 月度預算超限
    - 【處理逾時】：單次任務逾時
    - 【處理失敗】：未分類的後備訊息

    Example: 無法擷取任何文字的純圖片 PDF 歸類為【萃取失敗】
      Given 使用者 "free@example.com" 上傳一個無文字的 PDF 檔案
      When 背景處理執行完成
      Then 該資源的 status 應為 FAILED
      And 該資源的 error_message 應以「【萃取失敗】」開頭

  @added-by:cto
  Rule: 刪除考古題 Resource 後，重開知識地圖頁不得自動重建

    使用者刪除考古題題庫 Resource（type=markdown, name="{科目}考古題題庫"）後，
    重新進入該科目的知識地圖頁面時，系統不得因查無 Resource 而自動重建一份。
    考古題 Resource 的建立僅發生於明確的 onboarding 流程。

    背景：2026-04-20 用戶反映刪除考古題題庫後，資源列表又出現同內容項目。
    根因：knowledge_nav_service.get_nodes_by_subject() 每次都呼叫
    _ensure_exam_bank_resource(sid) 並 commit，會在 Resource 不存在時用
    新 UUID 重建，對使用者呈現為「刪除無效」。雲端 log 顯示同科目短時間內
    多筆不同 resource_id 的 INSERT。
    解法：移除 get_nodes_by_subject 中的 _ensure_exam_bank_resource 呼叫；
    _ensure_exam_bank_resource 仍保留給 onboarding 明確呼叫。

    另：GET /resources 亦不再將 subject_default_resources 以虛擬 id (hist:xxx)
    拼入回傳（獨立修正），列表只反映真實 Resource 表內容。

  # ─────────────────────────────────────────────
  # EPIC-035：資源上傳 LLM 統一解析 + 題庫自動抽取
  # ─────────────────────────────────────────────

  @epic-035
  Rule: 後置（查詢）- 解析完成後可查詢 parsed markdown 與狀態

    Example: 查詢已完成的解析狀態回傳 success + 內容型別
      Given 使用者 "pro@example.com" 已上傳資源 "LLM解析講義.pdf"（科目 ID: 1）並完成 LLM 解析，包含 2 個 T1 題、3 個 T2 題、1 個 T3 題
      When 使用者 "pro@example.com" 查詢該資源解析狀態
      Then 操作成功
      And 回應欄位 "status" 應為 "success"
      And 回應欄位 "detected_content_type" 應為 "mixed"

  @epic-035
  Rule: 後置（查詢）- 候選題依信度分桶；T1 已直接入個人題庫

    Example: 查詢候選題 T2/T3 分桶正確，T1 回傳 count
      Given 使用者 "pro@example.com" 已上傳資源 "LLM解析講義.pdf"（科目 ID: 1）並完成 LLM 解析，包含 2 個 T1 題、3 個 T2 題、1 個 T3 題
      When 使用者 "pro@example.com" 查詢該資源候選題
      Then 操作成功
      And 回應欄位 "t1_count" 應為 2
      And 回應的 "t2" 陣列應有 3 個項目
      And 回應的 "t3" 陣列應有 1 個項目

  @epic-035
  Rule: 後置（狀態）- 批次核可候選題寫入個人題庫並標記隔離

    Example: 核可 2 個 T2 候選題後進個人題庫且 never_for_scoring 正確
      Given 使用者 "pro@example.com" 已上傳資源 "LLM解析講義.pdf"（科目 ID: 1）並完成 LLM 解析，包含 0 個 T1 題、3 個 T2 題、0 個 T3 題
      When 使用者 "pro@example.com" 批次核可該資源前 2 個 T2 候選題
      Then 操作成功
      And 回應欄位 "approved" 應為 2
      And DB 中 source_resource_id=該資源 的 questions 應有 2 筆
      And 該 2 筆 questions 的 owner_user_id 應等於 "pro@example.com" 的 user_id

  @epic-035
  Rule: 前置（配額）- 超過月度 LLM 解析配額觸發 402 附升級引導

    Example: FREE 方案當月已用完 5 次解析，第 6 次觸發回 402
      Given 使用者 "free@example.com" 已上傳資源 "第六份.pdf"（科目 ID: 1）且有 0 個分塊
      And 使用者 "free@example.com" 本月已完成 5 次 LLM 資源解析
      When 使用者 "free@example.com" 觸發該資源的 LLM 解析
      Then 操作失敗狀態碼為 402
      And 錯誤訊息應包含「本月解析配額已用完」
      And 回應應包含升級引導欄位 "upgrade_hint"
