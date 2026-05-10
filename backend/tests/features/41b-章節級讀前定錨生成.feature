@feature_41b @chapter_anchor @k_re_01 @reverse_engineering @backend
Feature: K-RE-01 章節級讀前定錨生成（逆向工程科目）
  針對純逆向工程科目（無教材但有節點 + 考古題），
  用考古題群組生成章節級 advance_organizer。

  教學原理：Ausubel Subsumption Theory
  - advance_organizer 比要學的內容抽象一階
  - 提供「這一章在考什麼方向」的心智模型
  - 章節級（depth=1）優於節點級（depth=2）

  設計約束：
  - 1 個章節 → 1 個 advance_organizer
  - 80 字 hard limit（post-processor 強制截短）
  - resource_id = NULL（純逆向工程，無教材資源）
  - idempotent：重複呼叫同一章節不重複生成

  Background:
    Given 已存在 SUPER_ADMIN 用戶 "admin@certimate.tw"
    And 已存在 PRO 用戶 "alice@example.com"
    And 已存在逆向工程科目 "AI規劃師" 含 depth=1 章節與 depth=2 節點及考古題

  @backend
  Rule: 純逆向工程 subject 觸發成功（多章生成）

    Scenario: 對有考古題的章節成功生成 advance_organizer
      When 以 SUPER_ADMIN 呼叫 POST /api/v1/admin/scaffold-debug/generate-chapter-anchors/{subject_id}
      Then HTTP 200
      And 回應含 chapters_processed >= 1
      And 回應含 scaffolds_created >= 1
      And resource_scaffolds 新增 type='advance_organizer' template_code='K-RE-01'
      And scaffold 的 resource_id 為 NULL
      And scaffold_node_links 新增連結到該章下所有 nodes（包含 depth=1 章節本身）

  @backend
  Rule: 章節已有 K-RE-01 scaffold → skip（idempotent）

    Scenario: 重複觸發同一章節不重複生成
      Given 章節 "機器學習核心技術" 已有 template_code='K-RE-01' 的 advance_organizer
      When 以 SUPER_ADMIN 呼叫 POST /api/v1/admin/scaffold-debug/generate-chapter-anchors/{subject_id}
      Then HTTP 200
      And 回應含 skipped_already_exists >= 1
      And 回應含 scaffolds_created = 0
      And resource_scaffolds 不重複新增同章節 advance_organizer

  @backend
  Rule: 章節 0 考古題 → 不生成

    Scenario: 無考古題的章節被跳過
      Given 逆向工程科目含章節 "無題目章節" 無對應考古題
      When 以 SUPER_ADMIN 呼叫 POST /api/v1/admin/scaffold-debug/generate-chapter-anchors/{subject_id}
      Then HTTP 200
      And 回應含 skipped_no_questions >= 1
      And 該章節無 advance_organizer scaffold 被建立

  @backend
  Rule: 跨科目隔離

    Scenario: 科目 A 觸發不影響科目 B
      Given 另存在逆向工程科目 "B科目" 含章節與考古題
      And 科目 "AI規劃師" 已生成 advance_organizer scaffold
      When 以 SUPER_ADMIN 對科目 B 呼叫生成章節定錨端點
      Then HTTP 200
      And 科目 "AI規劃師" 的 advance_organizer scaffold 數量不變
      And 科目 "B科目" 的 advance_organizer scaffold 新增

  @backend
  Rule: e2e 可見性驗證

    Scenario: 生成後 GET /knowledge-map/nodes/{leaf_node_id}/scaffolds 含 advance_organizer
      Given 章節 "機器學習核心技術" 有子節點 "監督式學習"
      And 已對該科目成功觸發 K-RE-01 生成
      When 以 PRO 用戶呼叫 GET /api/v1/knowledge-map/nodes/{leaf_node_id}/scaffolds
      Then HTTP 200
      And 回應的 scaffolds 含至少 1 個 type='advance_organizer'
      And 該 scaffold 的 template_code = 'K-RE-01'

  @backend
  Rule: 鑑權

    Scenario: 非 SUPER_ADMIN 呼叫 → 403
      When 以 PRO 用戶呼叫 POST /api/v1/admin/scaffold-debug/generate-chapter-anchors/{subject_id}
      Then HTTP 403
      And 回應含 message "需要 SUPER_ADMIN 權限"

    Scenario: 無效 subject_id 格式 → 422
      When 以 SUPER_ADMIN 呼叫 POST /api/v1/admin/scaffold-debug/generate-chapter-anchors/not-a-uuid
      Then HTTP 422

    Scenario: 不存在 subject_id → 404
      When 以 SUPER_ADMIN 呼叫 POST /api/v1/admin/scaffold-debug/generate-chapter-anchors/00000000-0000-0000-0000-000000000999
      Then HTTP 404
      And 回應含 message "科目不存在"
