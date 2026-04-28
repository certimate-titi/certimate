@frontend
Feature: 資源庫管理與連鎖清除防呆機制

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |
      | 2        | bob@example.com    | PRO      |
    And 系統中有以下資源：
      | 資源 ID | 使用者 ID | 名稱                  | 類型    | 狀態      | 上傳時間            |
      | 1       | 1        | AWS_SAA_官方手冊.pdf  | PDF     | COMPLETED | 2024-01-05 10:00:00 |
      | 2       | 1        | 雲端概論筆記.md       | MD      | COMPLETED | 2024-01-08 14:00:00 |
      | 3       | 1        | 解析失敗的資料.pdf    | PDF     | FAILED    | 2024-01-09 09:00:00 |
      | 4       | 2        | Bob的AWS筆記.pdf      | PDF     | COMPLETED | 2024-01-06 11:00:00 |
      | 5       | 1        | AWS架構影片           | YouTube | COMPLETED | 2024-01-10 16:00:00 |

  # ========== 跨學科資源過濾 ==========

  Rule: 前置（導航）- 提供學科切換器過濾不同學科的資源列表

    Example: 切換學科後資源列表僅顯示該學科關聯的文件
      When 使用者在資源庫頁面選擇學科 "PMP"
      Then 資源列表應僅顯示 subjectId 為 "subj_pmp" 的資源
      And 資源列表不應包含 "AWS_SAA_官方手冊.pdf"

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 只能查看及管理自己的資源

    Example: 查詢自己的資源列表不應包含他人資源
      When 使用者 "alice@example.com" 查詢自己的資源列表
      Then 操作成功
      And 資源列表應只包含資源 ID 1、2、3、5
      And 資源列表不應包含資源 ID 4

  Rule: 前置（狀態）- 刪除他人資源失敗

    Example: 刪除其他使用者的資源失敗
      When 使用者 "alice@example.com" 刪除資源 4
      Then 操作失敗
      And 錯誤訊息應為 "無存取此資源的權限"

  # ========== 後置條件 ==========

  Rule: 後置（回應）- 查詢資源列表應回傳完整屬性包含狀態標籤

    Example: 查詢資源列表取得完整資源資訊
      When 使用者 "alice@example.com" 查詢自己的資源列表
      Then 操作成功
      And 資源列表應包含以下資源資訊：
        | 資源 ID | 名稱                  | 類型    | 狀態      | 上傳時間            |
        | 1       | AWS_SAA_官方手冊.pdf  | PDF     | COMPLETED | 2024-01-05 10:00:00 |
        | 2       | 雲端概論筆記.md       | MD      | COMPLETED | 2024-01-08 14:00:00 |
        | 3       | 解析失敗的資料.pdf    | PDF     | FAILED    | 2024-01-09 09:00:00 |
        | 5       | AWS架構影片           | YouTube | COMPLETED | 2024-01-10 16:00:00 |

  Rule: 後置（狀態）- 刪除 COMPLETED 資源時需彈出連鎖清除警告

    Example: 使用者嘗試刪除已完成解析的資源，系統彈出防呆確認
      When 使用者 "alice@example.com" 點擊刪除資源 1
      Then 系統應彈出防呆模態框
      And 模態框內容應警告：「此操作將同步刪除：① GCS 中的 .md 純文字紀錄、② pgvector 中的所有切塊向量、③ 衍生的心智圖知識節點、④ 相關聯的錯題排程紀錄。此操作無法復原。」

    Example: 使用者確認刪除後，系統依序執行連鎖清除
      Given 使用者已確認刪除資源 1 並勾選「我了解相關資料將永久清除」
      When 系統執行連鎖刪除
      Then 操作成功
      And GCS 中資源 1 的 .md 純文字紀錄應永久刪除
      And pgvector 中資源 1 關聯的所有 Embedding Chunks 應全數抹除
      And 資源 1 關聯的所有心智圖知識節點應標記為已刪除
      And 學習記憶排程中對應該資源考題的排程紀錄應連動撤銷

  Rule: 後置（狀態）- FAILED 資源可重新觸發解析，保留原始檔至成功為止

    Example: 對 FAILED 資源觸發重新解析後狀態重置為 PENDING，原始檔保留在 GCS
      When 使用者 "alice@example.com" 重新解析資源 3
      Then 操作成功
      And 資源 3 的狀態應重置為 "PENDING"
      And 資源 3 的原始 PDF 應仍保留於 GCS，等待重試完成

    Example: 重新解析成功後狀態更新為 COMPLETED，原始檔隨即從 GCS 刪除
      Given 資源 3 的狀態為 "PROCESSING"
      When 後端解析服務成功完成資源 3 的重試解析
      Then 資源 3 的狀態應更新為 "COMPLETED"
      And 資源 3 的原始 PDF 應從 GCS 永久刪除
      And 资源 3 應關聯至少一個新生成的心智圖知識節點

    Example: FAILED 資源刪除時無需彈出連鎖清除警告（尚無衍生資料）
      When 使用者 "alice@example.com" 刪除資源 3
      Then 操作成功
      And 資源 3 應標記為已刪除
      And 資源 3 的原始 PDF 應從 GCS 永久刪除

  Rule: 後置（軟隱藏 UX）- 刪除 platform 資源時應明確告知為「個人隱藏」非真刪除

    # 背景：scope='platform' 的資源（系統預載考古題題庫等）被多用戶共享，
    # 點刪除走 user_hidden_resources soft-hide。原本 confirm() 文案沒區分軟硬刪，
    # 導致使用者誤以為已徹底刪除無法還原。

    Example: 刪除 platform 資源時 confirm 應說明軟隱藏行為
      Given 資源 X 的 scope 為 "platform"
      When 使用者 "alice@example.com" 點擊資源 X 的「刪除」按鈕
      Then 應彈出 confirm 對話框
      And 對話框文案應包含「此操作只會從你的列表隱藏，不會真刪除原檔，可從『已隱藏資源』還原」

    Example: 刪除個人 / 機構資源時 confirm 維持原文案（真刪除）
      Given 資源 Y 的 scope 為 "personal"
      When 使用者 "alice@example.com" 點擊資源 Y 的「刪除」按鈕
      Then 應彈出 confirm 對話框
      And 對話框文案應包含「確定要刪除」（永久刪除提示）

  Rule: 後置（隱藏管理）- 提供「已隱藏資源」管理入口

    Example: 學習庫頁面提供「已隱藏資源」切換顯示
      When 使用者 "alice@example.com" 開啟資源庫頁面
      Then 頁面應提供「顯示已隱藏資源」切換開關（預設關閉）
      And 開啟切換後資源列表應顯示已隱藏項目，並標示「已隱藏」徽章
      And 已隱藏項目應提供「還原」按鈕

    Example: 還原已隱藏資源
      Given 使用者 "alice@example.com" 已隱藏資源 X
      When 使用者開啟「顯示已隱藏資源」並點擊資源 X 的「還原」按鈕
      Then 該筆 user_hidden_resources 紀錄應刪除
      And 資源 X 應重新出現在主要列表

  Rule: 後置（自我修復）- 系統應偵測檔案遺失並引導用戶重新上傳

    # 背景：dev/雲端環境若儲存體被清理或上傳中斷，DB 中的 gcs_path 會指向不存在的
    # 檔案。chunking 中繼產出（.md）可能已存在，但 LLM 鷹架（需重讀 PDF）會失敗。
    # 此 Rule 確保系統能主動辨識此類「孤兒資源」並引導使用者修復。

    Example: 列表 API 對「檔案遺失」資源回傳 needs_reupload=true
      Given 資源 X 的 gcs_path 對應檔案不存在
      And 資源 X 的最近一次 parse_job failure_reason 包含「檔案不存在」
      When 使用者 "alice@example.com" 查詢自己的資源列表
      Then 操作成功
      And 資源 X 的 needs_reupload 應為 true
      And 資源 X 的 scaffold_status 應為 "failed"

    Example: 「重新上傳」入口應在資源列表呈現
      Given 資源 X 的 needs_reupload 為 true
      When 使用者 "alice@example.com" 開啟資源庫頁面
      Then 資源 X 那一列應顯示「需重新上傳」徽章
      And 「解析內容」與「題目確認」連結應隱藏（避免引導至空鷹架）
      And 應提供一鍵刪除按鈕以便重新上傳

    Example: Admin healing endpoint 自動掃描並標記孤兒資源
      Given 系統中存在資源 Y，其 gcs_path 對應檔案不存在
      And 資源 Y 的 parse_job 狀態為 "success"（過去成功但檔案後來消失）
      When admin 觸發 POST /api/v1/admin/resources/heal-orphans
      Then 操作成功
      And 資源 Y 的最新 parse_job 應被新增一筆 status=failed、failure_reason="檔案不存在"

  Rule: 後置（API 契約）- 資源列表應反映「鷹架生成」子任務的真實狀態

    # 背景：resources.status 反映「整體可用性」（chunks/embeddings 是否就緒），
    # 但學習鷹架（scaffold）是 LLM 生成的子任務，可能獨立失敗。前端「解析內容」
    # 連結需要根據鷹架可用性決定啟用 / 隱藏，因此 API 必須回傳 scaffold_status。

    Example: 列表 API 回傳 scaffold_status 欄位
      When 使用者 "alice@example.com" 查詢自己的資源列表
      Then 操作成功
      And 每筆資源應包含 scaffold_status 欄位，值為下列之一：
        | 值       | 含意                                              |
        | ready    | 鷹架已生成（scaffold count > 0）                  |
        | pending  | 鷹架尚在處理（parse job pending / processing）    |
        | failed   | 鷹架生成失敗（parse job failed）                  |
        | none     | 此資源不適用鷹架（系統生成虛擬資源、YouTube 等）  |

  Rule: 後置（導航）- 「解析內容」入口應導向知識地圖並對焦該資源（連結語義承諾）

    # 連結文字「解析內容」承諾使用者按下後可看見：
    #   1. 該資源對應節點被選中
    #   2. 右側欄預設開啟「教材」分頁（學習鷹架）
    #   3. 教材內容非空（至少一項 takeaway / elaborative / strategy）
    # subjectId 必須隨連結傳遞，避免 active subject 與資源所屬科目不符時退回首筆

    @epic-035
    Example: 點擊「解析內容」按鈕跳轉至知識地圖並顯示學習鷹架
      Given 資源 1 屬於 subjectId "subj_aws"
      And 資源 1 已完成 LLM 解析，包含學習鷹架
      When 使用者 "alice@example.com" 在資源庫點擊資源 1 的「解析內容」按鈕
      Then 應導向 "/knowledge?subjectId=subj_aws&resourceId=1&tab=material"
      And 知識地圖頁應將 active subject 切換為 "subj_aws"
      And 知識地圖應自動展開並選中資源 1 對應的節點
      And 右側欄應預設顯示「教材」分頁
      And 教材分頁應顯示資源 1 對應節點的學習鷹架，且至少包含一項 takeaway / elaborative / strategy
      And 不應顯示「此節點尚未對應到教材鷹架」的空態文字

    @epic-035
    Example: 解析失敗的資源不顯示「解析內容」連結
      Given 資源 3 的狀態為 FAILED
      When 使用者 "alice@example.com" 開啟資源庫頁面
      Then 資源 3 那一列不應出現「解析內容」連結（避免引導至空鷹架頁）

    @epic-035
    Example: 鷹架生成失敗的資源「解析內容」連結應呈灰階且禁用
      Given 資源 X 的 scaffold_status 為 "failed"
      When 使用者 "alice@example.com" 開啟資源庫頁面
      Then 資源 X 那一列的「解析內容」連結應呈灰階且不可點擊
      And tooltip 應提示「鷹架生成失敗」

    @epic-035
    Example: 鷹架尚未生成的資源「解析內容」連結應呈灰階且禁用
      Given 資源 Y 的 scaffold_status 為 "pending"
      When 使用者 "alice@example.com" 開啟資源庫頁面
      Then 資源 Y 那一列的「解析內容」連結應呈灰階且不可點擊
      And tooltip 應提示「鷹架尚在處理中」

    @epic-035
    Example: 系統虛擬資源（考古題題庫）不顯示「解析內容」連結
      Given 資源 Z 的 scaffold_status 為 "none"
      When 使用者 "alice@example.com" 開啟資源庫頁面
      Then 資源 Z 那一列不應出現「解析內容」連結

  Rule: 後置（導航）- 「題目確認」入口應檢查資源是否有候選題

    Example: FAILED 或 PROCESSING 資源不顯示「題目確認」連結
      Given 資源 3 的狀態為 FAILED
      When 使用者 "alice@example.com" 開啟資源庫頁面
      Then 資源 3 那一列不應出現「題目確認」連結

    Example: 系統虛擬資源（考古題題庫）不顯示「題目確認」連結
      Given 資源 Z 的 type 為 "historical_exam" 或名稱結尾為 "題庫"
      When 使用者 "alice@example.com" 開啟資源庫頁面
      Then 資源 Z 那一列不應出現「題目確認」連結

  Rule: 後置（回應）- 搜尋資源時應依檔名與自動萃取的標籤進行篩選

    Example: 依關鍵字搜尋資源名稱取得符合結果
      When 使用者 "alice@example.com" 以關鍵字 "AWS" 搜尋資源列表
      Then 操作成功
      And 搜尋結果應包含資源 ID 1 和資源 ID 5
      And 搜尋結果不應包含資源 ID 2

    Example: 以標籤篩選資源取得符合結果
      Given 資源 1 帶有自動萃取的標籤 "EC2"、"S3"、"IAM"
      When 使用者 "alice@example.com" 以標籤 "EC2" 篩選資源列表
      Then 操作成功
      And 搜尋結果應包含資源 ID 1
  # ─────────────────────────────────────────────
  # PRD-033：多 scope 資源合併 + Ultra 分享給 EDU
  # ─────────────────────────────────────────────
  @prd-033 @wip
  Rule: GET /resources 需合併四種 scope 並附 badge

    Example: 使用者看到 personal + platform 預設 + institution + shared 四類
      Given 使用者 "u1@example.com" 有 2 個 personal 資源
      And 使用者的備考科目 "AI 應用規劃師（初級）" 綁定了 1 個 platform 預設資源
      And 使用者屬於機構 I1，機構有 1 個 institution 資源
      And Ultra 使用者 "ultra@example.com" 分享了 1 個資源給機構 I1 (scope=shared)
      When 使用者 "u1@example.com" 呼叫 GET /api/v1/resources
      Then 回應應包含 5 筆資源
      And badge 欄位應分別為 "personal"×2, "official_default"×1, "institution"×1, "edu_shared"×1
      And platform 與 shared 資源的 is_readonly 應為 true

  @prd-033 @wip
  Rule: Ultra 使用者可分享個人資源給特定 EDU 機構

    Example: Ultra 分享資源給目標機構
      Given 使用者 "ultra@example.com" 訂閱為 ULTRA_1599
      And 使用者擁有 personal 資源 R1
      When 呼叫 POST /api/v1/resources/{R1}/share-to-institution body={"institution_id": "I1"}
      Then 操作成功
      And 資源 R1 的 scope 應變為 "shared"
      And 資源 R1 的 target_institution_id 應為 "I1"

    Example: 非 Ultra 使用者無法分享
      Given 使用者 "pro@example.com" 訂閱為 PRO_199
      When 呼叫 POST /api/v1/resources/{R1}/share-to-institution
      Then 應回應 403
      And 錯誤訊息應包含 "僅 ULTRA 訂閱可分享資源"

    Example: Ultra 撤回分享
      Given 資源 R1 目前 scope=shared, target_institution_id=I1
      When 呼叫 DELETE /api/v1/resources/{R1}/share
      Then 操作成功
      And 資源 R1 的 scope 應還原為 "personal"
      And 資源 R1 的 target_institution_id 應為 NULL

  Rule: 後置（UI）- 「分享」按鈕應開啟 Modal 列出可選機構（取代 prompt UUID）

    # Spec 11 §ShareModal — 落地紀錄（2026-04-28）：
    # components/ShareToInstitutionModal.tsx 取代舊版 prompt() 直接輸入 UUID 的不安全流程。
    # 文案明確「分享給機構 → 該機構學生可看到」，因 EDU 用戶定位是學生不是機構 admin。

    Example: 點擊「分享」按鈕開啟機構選擇 Modal
      Given 使用者 "ultra@example.com" 為 ULTRA 訂戶且擁有資源 R1（scope=personal）
      When 使用者在資源庫點擊資源 R1 的「分享」按鈕
      Then 應開啟 ShareToInstitutionModal
      And Modal 應顯示資源名稱 R1
      And Modal 應載入並顯示已 DPA 簽署的機構列表
      And 每筆機構卡片應顯示：機構名稱、N 名學生
      And Modal 不應出現任何要求「輸入 UUID」的輸入框

    Example: 選擇機構並確認分享
      Given Modal 中列有機構 "XX 補習班" 含 42 名學生
      When 使用者點擊 "XX 補習班" 卡片
      Then 該卡片應呈藍色高亮並顯示確認文案：
        "將「<R1 名稱>」分享給「XX 補習班」，該機構 42 名學生將能看到此資源。"
      When 使用者點擊「確定分享」按鈕
      Then 系統應呼叫 POST /api/v1/resources/{R1}/share-to-institution
      And Modal 應顯示「✅ 分享成功！」並 1.2 秒後自動關閉
      And 主列表應 refresh

    Example: 機構列表載入失敗時 Modal 內呈現錯誤
      Given GET /resources/institutions/shareable 回傳 500
      When 使用者點擊「分享」按鈕
      Then Modal 應顯示錯誤訊息卡片含 AlertTriangle icon
      And 不應使用 alert() 跳出視窗

    Example: 撤回分享 confirm 文案應為「撤回對機構的分享」
      Given 使用者 "ultra@example.com" 的資源 R1 已分享（scope=shared）
      When 使用者在資源庫點擊資源 R1 的「分享」按鈕
      Then 應彈出 confirm 對話框
      And 文案應包含「撤回此資源對機構的分享」（不應出現「EDU」字樣，避免與 EDU 學生用戶混淆）
