# TiTi Prompt 模板管理

> **版本**：v1.0（2026-04-06）
> **維護原則**：此資料夾為所有 LLM 呼叫的 Prompt 模板 SSOT（唯一真實來源）。
> 後端 `prompt_templates` DB 表的初始資料由此資料夾 seed。

---

## 目錄結構

```
03_Prompt_Templates/
  README.md                          ← 本文件（索引 + 變數規範 + 微調指南）
  safety/
    S-01_safety_router.md            ← 三維度安全分類 Router
  knowledge/
    K-01_pdf_to_markdown.md          ← PDF 頁面轉 Markdown
    K-02_youtube_transcript.md       ← YouTube 逐字稿結構化
    K-03_knowledge_tree_extract.md   ← 知識節點樹萃取
    K-04_content_type_detect.md      ← 內容類型偵測
  exam/
    E-01_stage1_exam_point_analysis.md  ← 四階段 Pipeline：考點分析
    E-02_stage2_question_generation.md  ← 四階段 Pipeline：考題生成
    E-03_stage3_distractor_optimization.md ← 四階段 Pipeline：干擾項優化
    E-04_stage4_format_output.md        ← 四階段 Pipeline：格式化輸出
    E-05_syllabus_reverse_engineering.md ← 考綱逆向工程
    E-06_knowledge_tree_merge.md        ← 知識樹合併語意比對
  teaching/
    T-01_coach_basic.md              ← PRO_199 基礎教練
    T-02_coach_advanced.md           ← PRO_PLUS_399 完整教練（Certi 人格）
    T-03_wrong_answer_analysis.md    ← 錯題深度解析
    T-04_post_exam_summary.md        ← 考後總評
  emotion/
    F-01_encouragement.md            ← 打氣 / 慶祝 / 低谷關懷
    F-02_weekly_report.md            ← 學習週報
```

---

## Prompt 模板 Frontmatter 規範

每個 `.md` 檔案的 YAML frontmatter 欄位即為 `prompt_templates` DB 表的欄位：

```yaml
---
id: "S-01"                    # 唯一 ID，格式：{類別}-{序號}
name: "safety_router"         # 英文識別名
display_name: "三維度安全分類"  # 中文顯示名
category: "safety"            # safety / knowledge / exam / teaching / emotion
model: "gemini-flash"         # gemini-flash / claude-3.5-sonnet / vision / by-plan
max_tokens: 64                # 輸出上限
temperature: 0.0              # 0.0=確定性 / 0.3-0.5=穩健 / 0.7=創意 / 0.9=情感多樣
version: 1                    # 版本號（每次修改遞增）
feature_refs:                 # 關聯的 Feature 檔案
  - "07-錯題複習與AI教練"
  - "03b-知識心智圖導航"
variables:                    # 動態變數清單
  - name: "subject_name"
    description: "當前備考科目名稱"
    example: "AWS SAA"
  - name: "exam_status"
    description: "考試狀態"
    example: "IN_PROGRESS"
---
```

---

## 動態變數規範

### 全域共用變數

| 變數 | 型別 | 說明 | 注入來源 |
| :--- | :--- | :--- | :--- |
| `{subject_name}` | string | 當前科目名稱 | DB: subjects.name |
| `{user_input}` | string | 用戶輸入（已截斷至 500 字） | API request body |
| `{user_background_instruction}` | string | 個人化背景指令（可為空） | DB: user_profiles |

### 教練專用變數

| 變數 | 型別 | 說明 |
| :--- | :--- | :--- |
| `{node_name}` | string | 當前知識節點名稱 |
| `{mastery_rate}` | int | 當前節點掌握度 (0-100) |
| `{source_content}` | string | 溯源內容（Markdown 格式） |
| `{exam_status}` | enum | IN_PROGRESS / SUBMITTED / null |

### 出題專用變數

| 變數 | 型別 | 說明 |
| :--- | :--- | :--- |
| `{bloom_instruction}` | string | Bloom 配比指令 |
| `{difficulty_distribution}` | string | 難度分布 |
| `{vectorized_content}` | string | 從 pgvector 檢索的知識片段 |
| `{stage{N}_output}` | JSON | 上一階段的輸出 |
| `{custom_instruction}` | string | 管理員自訂指令（來自 DB） |

---

## 微調指南

### 方式 1：直接修改（即時生效）

1. 編輯對應的 `.md` 檔案
2. 遞增 frontmatter 中的 `version`
3. 執行 `python -m app.scripts.seed_prompts` 同步至 DB

### 方式 2：管理後台修改（即時生效）

1. 登入管理後台 → 系統設定 → Prompt 模板管理
2. 選擇模板 → 編輯 → 儲存
3. 系統自動 version++ 並記錄歷史版本

### 方式 3：A/B 測試

1. 管理後台 → 選擇模板 → 建立 A/B 測試
2. 設定 variant B 的 prompt 與流量比例
3. 追蹤指標（答題正確率、用戶滿意度、API 成本）
4. 勝者自動上線

### Temperature 調整原則

| 場景 | 建議值 | 原因 |
| :--- | :--- | :--- |
| 分類/偵測/格式化 | 0.0 | 需要確定性輸出 |
| 知識萃取/分析 | 0.1-0.3 | 結構化但允許微量變化 |
| 錯題解析/教練對話 | 0.5-0.7 | 需要解釋多樣性 |
| 出題（題幹+干擾項） | 0.7 | 需要創意但不偏離事實 |
| 鼓勵/情感化 | 0.9 | 最大化語氣多樣性 |
