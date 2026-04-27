# TiTi 出題品質保障規格書

> **版本**：v3.0 | 2026-04-03
> **負責角色**：⭐考題設計人員
> **OKR 對齊**：O1-KR1（答案正確率 ≥ 95%）、O1-KR3（信度標示 100%）
>
> **核心原則**：原始資料轉換正確 > 事後清洗。
> 詳見 `pdf-to-markdown-spec.md` — 使用 LLM 進行 PDF → MD 結構化轉換，
> 而非依賴 regex 分割 + 事後清洗。

---

## 一、四層品質保障框架

```
Layer 1：匯入時品質閘門 ── 考古題進 DB 前自動驗證
Layer 2：AI 生成後驗證 ── Cross-LLM 交叉驗證
Layer 3：使用者反饋迴圈 ── 答題行為驅動品質偵測
Layer 4：定期品質審計 ── 考題設計人員月度審核
```

---

## 二、Layer 1 — 匯入時品質閘門

### 5 項自動檢查

每道考古題進入 DB 前必須通過：

| # | 檢查項 | 規則 | 不通過處置 |
|---|--------|------|----------|
| 1 | 題幹完整性 | length ≥ 10 字 + 不以碎片字開頭 | `quality_flag = "review"` |
| 2 | 四選項完整 | A/B/C/D 各 ≥ 2 字，各 ≤ 200 字 | 同上 |
| 3 | 答案有效性 | correct_answer ∈ {A, B, C, D} | 拒絕匯入 |
| 4 | 選項不重複 | 4 選項互不相同 | `quality_flag = "review"` |
| 5 | 頁首殘留 | 不含「頁，共」「公告試題」「答案 題 目」 | 自動清洗後重試 |

### 品質等級

```
✅ ok       — 通過全部 5 項 → 直接匯入
⚠️ review   — 1-2 項不通過 → 匯入但標記待審
❌ rejected — 答案無效或嚴重截斷 → 不匯入
```

---

## 三、Layer 2 — AI 生成後 Cross-LLM 驗證

### 核心原則：出題和驗證必須使用不同 LLM

```
出題（Model A）──→ 題目 ──→ 驗證（Model B）──→ 結果
                                │
                     ┌──────────┼──────────┐
                     ▼          ▼          ▼
                  ✅ PASS    ⚠️ REVIEW   ❌ REJECT
                  答案一致    答案不一致   結構有誤
```

### 模型配對規則

**原則**：驗證使用低階模型，控制成本。出題用強模型確保品質，驗證只需判斷對錯。

| 出題模型 | 驗證模型（低階） | 成本/題 |
|---------|----------------|--------|
| Claude Sonnet/Opus | **Gemini Flash** | ~$0.0005 |
| Gemini Pro | **Claude Haiku** | ~$0.001 |
| GPT-4o | **Gemini Flash** | ~$0.0005 |

**絕對禁止**：同一家廠商的模型出題又驗證（避免同源偏差）。
**成本上限**：驗證模型限定 Haiku / Flash / GPT-4o-mini 等級，不使用 Opus / Pro / GPT-4o。

### 驗證 Prompt

```
System:
  你是考題品質審查員。你的工作是獨立判斷以下選擇題的正確性。
  不要假設提供的答案是對的——你必須自己推理出正確答案。

User:
  【題目】{content}
  (A) {option_a}
  (B) {option_b}
  (C) {option_c}
  (D) {option_d}

  請完成以下檢查，回傳純 JSON：
  {
    "your_answer": "A/B/C/D",          // 你認為的正確答案
    "confidence": "high/medium/low",    // 你的信心度
    "reasoning": "簡短推理過程",
    "issues": [                         // 品質問題列表（空 = 無問題）
      "選項 C 與 D 語意過於接近",
      "題幹不完整"
    ]
  }
```

### 驗證結果處理

```python
def process_validation(generated_answer: str, validator_result: dict) -> str:
    validator_answer = validator_result["your_answer"]
    confidence = validator_result["confidence"]
    issues = validator_result["issues"]

    if generated_answer == validator_answer and not issues:
        return "ok"           # ✅ 兩模型一致 + 無品質問題

    if generated_answer != validator_answer:
        if confidence == "high":
            return "replace"  # ❌ 驗證模型高信心不同意 → 抽換為其他題目
        else:
            return "review"   # ⚠️ 低信心不同意 → 人工確認

    if issues:
        return "review"       # ⚠️ 有品質問題但答案一致

    return "ok"
```

### 異常題目處置原則

**核心原則：異常題自動抽換，不減少出題數量。**

```
偵測到異常題 → 從題庫/AI 補抽一題替換 → 維持總題數不變
```

| 驗證結果 | 處置 | 說明 |
|---------|------|------|
| `ok` | 直接出題 | 無需處理 |
| `review` | 出題但標記待審 | 不影響使用者體驗，後台排隊人工審核 |
| `replace` | **抽換為其他題目** | 從同節點題庫隨機補一題，確保總數不變 |

```python
def handle_validation_result(question, result, node_pool):
    if result == "replace":
        # 從同節點的考古題庫抽一題替換
        replacement = node_pool.get_random_excluding(question.id)
        if replacement:
            return replacement  # 用替換題
        # 無可用替換 → 降級為 review（仍出題，但標記）
        question.quality_flag = "review"
        return question
    elif result == "review":
        question.quality_flag = "review"
        return question
    else:
        return question  # ok
```

### 成本控制策略

| 策略 | 說明 |
|------|------|
| **全量驗證 🟡 AI 題** | 所有 AI 生成的題目都做 Cross-LLM 驗證 |
| **抽檢 🟢 考古題** | 每次匯入抽 10% 做 LLM 驗證（答案可能標記錯誤） |
| **使用便宜模型驗證** | 驗證用 Gemini Flash / Haiku（不需要最強模型） |
| **批次驗證** | 每 10 題一次 API 呼叫（減少 overhead） |

### 驗證模型成本估算（限定低階模型）

| 驗證模型 | 每題成本 | 20 題考卷 | 月 1000 題 |
|---------|---------|---------|-----------|
| **Gemini Flash**（首選） | ~$0.0005 | $0.01 | **$0.50** |
| Claude Haiku | ~$0.001 | $0.02 | $1.00 |
| GPT-4o mini | ~$0.0005 | $0.01 | $0.50 |

**結論**：每月驗證成本 < $1，佔 LLM 總成本 < 1%。
**董事會成本指令**：驗證一律使用低階模型（Flash/Haiku/mini），禁止用 Opus/Pro/GPT-4o 驗證。

---

## 四、Layer 3 — 使用者反饋迴圈

### 自動偵測異常題目

| 信號 | 觸發條件 | 嚴重度 | 行動 |
|------|---------|--------|------|
| 答對率 = 0% | ≥10 人作答，0 人答對 | 🔴 | 自動 flag + 停用 |
| 答對率 = 100% | ≥10 人作答，全對 | 🟡 | 標記太簡單 |
| A 選率 > 80% | 單一選項被選比例異常 | 🟡 | 檢查是否答案明顯 |
| 跳過率 > 30% | 太多人跳過此題 | 🟡 | 檢查題幹是否完整 |
| 使用者回報 | AI 教練對話中提到「答案錯」 | 🟡 | 人工審核 |

### 偵測 SQL（每日排程）

```sql
SELECT q.id, q.content, q.correct_answer, q.quality_flag,
  COUNT(*) AS total_answers,
  ROUND(AVG(CASE WHEN a.is_correct THEN 1.0 ELSE 0.0 END) * 100, 1) AS correct_pct,
  ROUND(MAX(CASE WHEN a.selected_answer = q.correct_answer THEN 0 ELSE 1 END) * 100.0, 1) AS wrong_pct
FROM questions q
JOIN answers a ON a.question_id = q.id
GROUP BY q.id
HAVING COUNT(*) >= 10
AND (
  AVG(CASE WHEN a.is_correct THEN 1.0 ELSE 0.0 END) = 0       -- 0% 答對
  OR AVG(CASE WHEN a.is_correct THEN 1.0 ELSE 0.0 END) = 1    -- 100% 答對
)
ORDER BY COUNT(*) DESC;
```

### DB 欄位（需 migration）

```sql
ALTER TABLE questions ADD COLUMN quality_flag VARCHAR(20) DEFAULT 'ok';
ALTER TABLE questions ADD COLUMN flag_reason TEXT;
ALTER TABLE questions ADD COLUMN flagged_at TIMESTAMPTZ;
ALTER TABLE questions ADD COLUMN validation_model VARCHAR(50);
ALTER TABLE questions ADD COLUMN validation_result JSONB;
```

---

## 五、Layer 4 — 定期品質審計

### 月度審計模板

```markdown
# 📊 題庫品質月報 — {YYYY-MM}

## 概況
| 指標 | 本月 | 目標 | 趨勢 |
|------|------|------|------|
| 🟢 考古題答案正確率 | {%} | ≥ 99% | |
| 🟡 AI 題答案正確率 | {%} | ≥ 95% | |
| Cross-LLM 不一致率 | {%} | < 5% | |
| 使用者回報問題數 | {N} | < 5/月 | |
| 異常答對率題目 | {N} | < 10 | |
| 品質 flagged 題目 | {N} | < 20 | |

## 本月標記的問題題
| ID | 類型 | 問題 | 處置 |
|----|------|------|------|

## Bloom 分佈偏移
| 科目 | remember 目標/實際 | apply 目標/實際 | 偏移量 |
|------|-------------------|----------------|--------|

## 下月行動
- [ ] {行動 1}
```

---

## 六、品質驗證流程整合到出題 Pipeline

```
混合式出題 Pipeline v2.0
          │
    ┌─────▼─────────────────────────┐
    │ 20% 考古題抽取                 │
    │ → Layer 1 閘門已在匯入時通過   │
    │ → 標記 reliability = "green"   │
    └─────┬─────────────────────────┘
          │
    ┌─────▼─────────────────────────┐
    │ 80% AI 生成（Model A）         │
    │ → Layer 2 Cross-LLM 驗證       │
    │   └─ Model B 獨立判斷答案      │
    │   └─ 一致 → reliability="yellow"│
    │   └─ 不一致 → quality_flag=     │
    │      "review" + 人工後續處理    │
    └─────┬─────────────────────────┘
          │
    ┌─────▼─────────────────────────┐
    │ 交錯排列 + 呈現給使用者        │
    │ → Layer 3 開始收集答題數據      │
    └─────┬─────────────────────────┘
          │
    ┌─────▼─────────────────────────┐
    │ 每月 → Layer 4 品質審計         │
    └─────────────────────────────────┘
```

---

## 七、Cross-LLM 驗證的後端實作位置

```python
# ai_generation_service.py → _generate_ai_for_node()

def _validate_with_cross_llm(self, questions: list[dict], generation_model: str) -> list[dict]:
    """用不同 LLM 驗證 AI 生成的題目"""

    # 選擇驗證模型（不同於出題模型）
    validator = self._get_validator_model(generation_model)
    # "claude" → use "gemini"
    # "gemini" → use "claude"
    # "openai" → use "claude"

    for q in questions:
        result = validator.generate_json(
            VALIDATION_SYSTEM_PROMPT,
            format_validation_prompt(q),
        )
        q["validation_model"] = validator.model_name
        q["validation_result"] = result

        if result["your_answer"] != q["correct_answer"]:
            q["quality_flag"] = "review" if result["confidence"] != "high" else "flagged"
        else:
            q["quality_flag"] = "ok"

    return questions
```

---

## 八、實作優先順序

| 優先 | Layer | 項目 | 工期 | 角色 |
|------|-------|------|------|------|
| 1 | L1 | `validate_question()` 匯入閘門函式 | 0.5 天 | 考題設計 |
| 2 | L2 | Cross-LLM 驗證 Prompt + 模型配對 | 1 天 | 考題設計 + Prompt |
| 3 | L2 | `_validate_with_cross_llm()` 後端整合 | 1 天 | 後端研發 |
| 4 | DB | `quality_flag` + `validation_result` migration | 0.5 天 | 後端研發 |
| 5 | L3 | 異常答對率 SQL 排程 | 1 天 | 後端研發 |
| 6 | L3 | 使用者回報 → 自動標記 | 1 天 | 後端 + 前端 |
| 7 | L4 | 月報模板 + 自動統計腳本 | 1 天 | 考題設計 |
| **合計** | | | **~6 天** | |

---

## 九、事故檢討與防止再發（Post-Mortem）

> 本章記錄實際發生的品質事故，作為後續匯入新科目考古題時的必讀 checklist。

### 事故 1：PDF 頁首混入題目內容（2026-04-03）

**現象**：
考古題模擬考的題目顯示為：
```
「第 5 頁，共 13 頁 114 年第四次 AI 應用規劃師-初級能力鑑定【公告試題】
第一科：人工智慧基礎概論 考試日期：114年11月01日 答案 題 目
哪種資料處理策略屬於常見的「資料去偏」做法？」
```

**根因**：
- iPAS PDF 每頁都有頁首：年份、科目、考試日期、「答案 題 目」
- PDF 解析器 `parse_exam_pdf.py` 在拼接全文後沒有清除頁首
- 頁首文字被混入題幹的 `content` 欄位

**修正**：
- 新增 `_clean_page_headers()` 函式，支援 iPAS/SFI/考選部 三種格式
- 使用逐行 regex 清除（不用 DOTALL），避免吃掉題目內容
- 在 SFI、iPAS、考選部三個解析器中統一加上清洗步驟

**防止再發**：
- ✅ Layer 1 閘門檢查 `pollution_keywords`（頁，共/公告試題/答案 題 目）
- ✅ 新增科目的 PDF 匯入前，必須先用 `validate_question()` 跑過全部題目
- ✅ 任何殘留頁首的題目自動標記 `quality_flag = "review"`

---

### 事故 2：選項 D 溢出混入下一題（2026-04-03）

**現象**：
選項 D 顯示為：
```
「KL散度（Kullback-Leibler Divergence） 某醫院希望開發一個系統，
根據患者的年齡、血壓與 BMI等資訊，預測...」
```

**根因**：
- PDF 解析器用題號分割文字（`[A-D] \d+.`）
- 最後一個選項（D）的結尾界定依賴「下一題的開始」
- 但跨頁時，下一題的開始被頁首干擾，分割點後移
- 結果：選項 D 吃到了下一題的題幹

**修正**：
- 新增 `_truncate_option_overflow()` 函式
- 超過 200 字的選項自動在分號/句號後截斷
- 偵測下一題特徵詞（某公司/某團隊/下列/關於）並截斷

**防止再發**：
- ✅ Layer 1 閘門檢查 `option_d 長度 > 200 字`
- ✅ 超長選項自動標記 `quality_flag = "review"`

---

### 事故 3：題幹跨頁截斷（2026-04-03）

**現象**：
題目顯示為：
```
「數（Loss Function）來衡量預測誤差？」
```
前面缺了「下列哪一種損失函」。

**根因**：
- iPAS 格式「答案在前」（`B 16.`），解析器用此 pattern 分割
- 題目 16 的題幹橫跨 page 3→4，前半段在 page 3 最後幾行
- 分割後，前半段被歸入上一題的「raw text」末尾
- 結果：題目 16 只拿到後半段

**修正**：
- 新增 `_clean_question_content()` 函式
- 偵測題幹開頭是否為碎片（不以常見問句模式開頭）
- 嘗試找到真正的問句起點並截斷前置碎片
- **本質限制**：跨頁的前半段已丟失，無法完全恢復

**防止再發**：
- ✅ Layer 1 閘門檢查 `content 長度 < 10 字`
- ✅ 檢查題幹開頭是否為常見截斷碎片字（數/列/者/項）
- ✅ 不完整題目標記 `quality_flag = "review"`，不進入考古題模擬考
- ⚠️ **已知限制**：iPAS PDF 跨頁題目的前半段無法自動恢復，需要人工審核

---

### 事故 4：考試結果顯示「10 題未答」（2026-04-03）

**現象**：
使用者全部作答完畢，但結果頁顯示「3 答對、0 答錯、10 未答」。

**根因**：
- 後端 `ExamResultService.get_result()` 沒有回傳 `user_answers` 欄位
- 前端 fallback 產生 10 個 `userChoice: null` 的假資料
- `userChoice: null` 被前端計為「未答」

**修正**：
- 後端 `get_result()` 新增 `user_answers` 陣列回傳（含 userChoice、isCorrect）
- 同時新增 `time_spent_seconds` 和完整 `questions` 資料

**防止再發**：
- ✅ 前端不再依賴 fallback 假資料
- ✅ Feature 06-測驗結果 應覆蓋此 scenario（待補 BDD 測試）

---

### 事故 5：AI 出題全是假題（2026-04-03）

**現象**：
所有題目都是「關於「{考點}」的核心概念，以下何者正確？」模板。

**根因**：
- `AiGenerationService` 的 4 階段 Pipeline 走了 fallback 路徑
- 無 LLM API key 或 Claude 呼叫失敗時，Stage 2 生成模板假題
- 模板固定為 `「關於{point_name}的核心概念」`，無實質內容

**修正**：
- 實作混合式 Pipeline：20% 考古題 + 80% AI
- 無 LLM 時不再用模板，改為從考古題池擴大抽取
- 新增 `_fill_shortfall()` 三級補題策略

**防止再發**：
- ✅ 出題引擎規格書原則 1：禁止模板 Fallback 上線
- ✅ 無 LLM + 無考古題 → 回傳明確錯誤訊息
- ✅ AI 生成不足時自動從考古題池補題

---

## 十、新科目匯入 Checklist

> 每次匯入新科目考古題時，**必須依序執行**以下檢查：

### 匯入前

- [ ] **Step 1**：用 `pdfplumber` 檢查 PDF 前 3 頁文字結構
  - 確認頁首格式（每個來源不同）
  - 確認題號格式（`1.` / `A 1.` / `(1)` 等）
  - 確認選項格式（`(A)` / `①` / 純文字）
- [ ] **Step 2**：確認 `_clean_page_headers()` 覆蓋此 PDF 的頁首模式
  - 若不覆蓋 → 新增 regex 到清洗函式
- [ ] **Step 3**：用 `parse_exam_pdf.py` 解析，檢查 JSON 品質
  - 題數是否合理（對照原始 PDF 題數）
  - 有答案比例是否正常
- [ ] **Step 4**：用 `validate_question()` 跑過全部題目
  - ok 率應 ≥ 85%
  - rejected 應 = 0
  - review 題抽 5 題人工確認

### 匯入中

- [ ] **Step 5**：匯入時寫入 `quality_flag`（ok/review/rejected）
- [ ] **Step 6**：rejected 題不匯入 DB
- [ ] **Step 7**：連結 `node_id` 到正確的知識節點
- [ ] **Step 8**：更新 `knowledge_nodes.available_questions` 計數（僅 ok 題）

### 匯入後

- [ ] **Step 9**：用考古題模擬考模式出 20 題測試
  - 確認題目完整（無截斷、無頁首）
  - 確認選項 4 個都有且合理
  - 確認答案正確
- [ ] **Step 10**：記錄匯入結果到品質月報

```
匯入紀錄：
  科目：{name}
  日期：{date}
  PDF 數：{N}
  解析題數：{N}
  ok：{N} ({%})
  review：{N} ({%})
  rejected：{N}
  匯入人：{name}
```
