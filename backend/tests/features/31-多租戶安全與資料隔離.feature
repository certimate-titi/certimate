# Feature 31 — 多租戶安全與資料隔離
# 對應 ToDoList.md 階段一至四的安全需求
# 🧭 目標對齊：O3 - KR1（LLM API 成本佔營收 ≤ 15%）+ O2 - KR1（付費用戶擴增）
# 涵蓋：RLS 隔離、HNSW 向量索引、SSRF 防護、JWT tenant_id、退場抹除

@tenant_security
Feature: 多租戶安全與資料隔離
  作為平台管理員
  我希望系統能強制執行多租戶資料隔離
  以確保不同機構的題庫、成績、向量資料不會相互洩漏

  Background:
    Given 系統已有兩個活躍租戶
      | slug         | name         | plan_tier   |
      | company_a    | A 公司教育部   | b2b_pro     |
      | company_b    | B 補習班      | b2b_basic   |
    And 每個租戶各有 1 名學生用戶

  # ─────────────────────────────────────────────
  # Rule: 租戶資料 Schema 埋點（階段一）
  # ─────────────────────────────────────────────
  Rule: 所有業務資料表必須含有 tenant_id 欄位

    Example: 新建資源時自動標記 tenant_id
      Given 租戶 "company_a" 的學生已登入，JWT 含 tenant_id
      When 學生上傳一份 PDF 資源「會計學原理.pdf」
      Then resources 表中該筆資料的 tenant_id 應等於 company_a 的 UUID
      And resource_chunks 表中該資源的所有 chunks 的 tenant_id 亦應等於 company_a 的 UUID

    Example: 預設 B2C 散客的 tenant_id 為 public_b2c
      Given B2C 散客用戶已登入，JWT 不含 tenant_id
      When 散客上傳一份 PDF 資源「金融法規.pdf」
      Then resources 表中該筆資料的 tenant_id 應等於 public_b2c 的 UUID

  # ─────────────────────────────────────────────
  # Rule: RLS 資料物理隔離（階段一）
  # ─────────────────────────────────────────────
  Rule: 不同租戶的向量資料和成績資料必須物理隔離

    Example: 租戶 A 無法查詢租戶 B 的 resource_chunks
      Given 租戶 "company_a" 已上傳資源並建立了 10 個 chunks（tenant_id = company_a）
      And 租戶 "company_b" 已上傳資源並建立了 8 個 chunks（tenant_id = company_b）
      When 以租戶 "company_a" 的 DB Session（app.current_tenant_id = company_a）查詢全部 resource_chunks
      Then 查詢結果應只包含 company_a 的 10 個 chunks
      And 不應看到 company_b 的 8 個 chunks

    Example: 租戶 A 無法讀取租戶 B 學生的作答記錄
      Given 租戶 "company_b" 的學生完成一份考試並留下 answers 記錄
      When 以租戶 "company_a" 的 DB Session 查詢 answers 表
      Then 查詢結果不應包含 company_b 學生的 answers

  # ─────────────────────────────────────────────
  # Rule: JWT tenant_id 宣告（階段二）
  # ─────────────────────────────────────────────
  Rule: JWT Token 必須攜帶 tenant_id 宣告

    Example: 登入後取得含 tenant_id 的 JWT
      Given 租戶 "company_a" 的學生使用有效帳密登入
      When POST /api/v1/auth/login
      Then 回應 JWT payload 應包含 "tenant_id" 欄位
      And "tenant_id" 值應等於 company_a 的 UUID

    Example: 不攜帶 tenant_id 的舊 Token 向後相容
      Given 一個不含 tenant_id 的舊格式 JWT（只有 sub 欄位）
      When 使用該 Token 呼叫 GET /api/v1/resources
      Then 系統應成功回應 200
      And 系統應將此請求視為 public_b2c 租戶（向後相容）

  # ─────────────────────────────────────────────
  # Rule: SSRF 安全防護（階段一）
  # ─────────────────────────────────────────────
  Rule: 用戶輸入的 URL 必須通過 SSRF 防護驗證

    Example: 阻擋指向內網的 YouTube URL 偽裝攻擊
      Given 已登入的用戶
      When 用戶提交 URL "http://192.168.1.1/video" 作為 YouTube 資源
      Then 系統應回應 422 Unprocessable Entity
      And 錯誤訊息應包含 "URL 指向內網" 或 "不是有效的 YouTube URL"

    Example: 阻擋指向 Cloud Metadata 服務的攻擊
      Given 已登入的用戶
      When 用戶提交 URL "http://169.254.169.254/latest/meta-data/" 作為 YouTube 資源
      Then 系統應回應 422 Unprocessable Entity
      And 錯誤訊息應包含 "受保護的內部服務"

    Example: 允許合法的 YouTube URL
      Given 已登入的用戶
      When 用戶提交 URL "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 作為 YouTube 資源
      Then 系統應通過 SSRF 驗證並開始處理

  # ─────────────────────────────────────────────
  # Rule: 租戶資料退場抹除（階段四）
  # ─────────────────────────────────────────────
  Rule: 解約的企業租戶資料必須能被完整物理清除

    Example: 執行租戶資料抹除腳本（需要 --confirm）
      # 此 scenario 模擬退場流程，正式執行需管理員確認
      Given 租戶 "company_b" 已解約，系統標記為待清除
      When 執行 purge_tenant_data.py --tenant-id company_b --dry-run
      Then 腳本應列出 company_b 的所有資料統計
      And 不應實際刪除任何資料（dry-run 模式）

    Example: 禁止刪除 public_b2c 預設租戶
      Given 嘗試呼叫 purge_tenant_data 腳本，目標為 tenant_id = "00000000-0000-0000-0000-000000b2cb2c"
      When 腳本執行
      Then 腳本應拋出 ValueError 並終止
      And 錯誤訊息應包含 "禁止刪除 public_b2c"

  # ─────────────────────────────────────────────
  # Rule: BDD 測試環境隔離（階段四）
  # ─────────────────────────────────────────────
  Rule: BDD 測試資料不得污染正式環境資料

    Example: 每個 Scenario 使用獨立的測試租戶
      Given BDD 測試環境已初始化
      When 查看 context.test_tenant_id
      Then test_tenant_id 應不等於 public_b2c 的 UUID
      And test_tenant_id 應為有效的 UUID 格式

    Example: Scenario 結束後測試資料被完整清理
      Given 測試 Scenario 已建立 5 筆 resources（tenant_id = test_tenant）
      When after_scenario 鉤子執行 TRUNCATE
      Then resources 表中不應有任何 tenant_id = test_tenant 的資料殘留

  # ─────────────────────────────────────────────
  # PRD-033：多租戶 tenant_id 補正與 RLS 容錯（Migration 061）
  # ─────────────────────────────────────────────
  @prd-033 @wip
  Rule: 既有資料的 tenant_id NULL 值必須回填

    Example: Migration 061 回填 5 張表的 NULL tenant_id
      Given 資料表 resources, subjects, user_subjects, exams, questions 於歷史資料中存在 tenant_id IS NULL 的列
      When Alembic upgrade 到 revision 061
      Then 5 張表中不應再有 tenant_id IS NULL 的列
      And 所有被回填的列的 tenant_id 應為 PUBLIC_B2C_TENANT_ID ("00000000-0000-0000-0000-000000b2cb2c")
      And 5 張表的 tenant_id 欄位應設為 NOT NULL DEFAULT PUBLIC_B2C_TENANT_ID

  @prd-033 @wip
  Rule: RLS policy 必須容錯 app.current_tenant_id GUC 為空字串

    Example: 未設定 GUC 時 RLS 不應拋出 UUID cast 錯誤
      Given PostgreSQL session 未呼叫 SET app.current_tenant_id
      When 對 resources 表執行 SELECT
      Then 查詢不應拋出 "invalid input syntax for type uuid" 錯誤
      And RLS 應視為 tenant_id = PUBLIC_B2C_TENANT_ID
