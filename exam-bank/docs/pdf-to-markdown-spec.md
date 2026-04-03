# TiTi PDF → Markdown 轉換規格書

> **版本**：v2.0 | 2026-04-03
> **核心原則**：原始資料轉換正確 > 事後清洗
> **負責角色**：⭐考題設計人員 + 後端研發

---

## 一、策略演進

### v0 — regex 解析（已棄用）

```
PDF ──pdfplumber──→ 純文字拼接 ──regex 分割──→ 碎片題目 ──事後清洗──→ 勉強可用
問題：跨頁截斷、頁首混入、數學式丟失
```

### v1 — Claude Sonnet LLM 轉換（已棄用）

```
PDF ──pdfplumber──→ 每頁原始文字 ──Claude Sonnet 分批──→ Markdown ──簡單解析──→ 完整題目
問題：速度慢（15-30秒）、成本高（$0.06/份）、仍需文字提取步驟
```

### v2 — Gemini Flash 原生 PDF（正式採用）

```
PDF ──Gemini Flash 原生上傳──→ Stage 0 偵測 content_type ──→ 對應 Prompt 轉換 ──→ MD + 4 層驗證
                                    │
                                    ▼
                    7 種內容類型 × 7 種專用 Prompt
                    exam | regulation | textbook | summary
                    formula | syllabus | general
```

**優勢**：
- **原生 PDF 上傳**：Gemini 直接讀取 PDF，不經 pdfplumber，數學式不丟失
- **內容感知**：依 content_type 選擇最適合的轉換 Prompt
- **成本**：$0.005/份（v1 的 1/12）
- **品質**：4 層自動驗證閘門
- **轉換器**：`exam-bank/parsers/gemini_pdf_converter.py`

### 7 種 Content Type 對應 Prompt

| ContentType | Prompt 重點 | 產出格式 |
|-------------|-----------|---------|
| exam | 題幹+選項+答案結構化 | `## 題號. 題幹` + `- (A)` + `**答案：X**` |
| regulation | 條文結構保留（編/章/節/條） | `## 第 N 條` + 項/款/目 |
| textbook | 章節層級 + 定義/範例標記 | `# 章` + `## 節` + `> 定義：` |
| summary | 要點條列 + 記憶法 | `## 主題` + `- **重點**：` |
| formula | KaTeX 公式 + 變數說明 | `## 公式名稱` + `$$公式$$` + 變數表 |
| syllabus | 考科+主題+權重 | `# 考試` + `## 考科` + 百分比 |
| general | 基礎結構化 | 標題層級 + 表格 |

---

## 二、Pipeline

```
Step 1: pdfplumber 提取每頁原始文字
Step 2: 每 4-5 頁為一批，送 LLM 轉換為結構化 MD
Step 3: 合併所有批次的 MD
Step 4: 從 MD 用簡單 regex 提取題目 → JSON
Step 5: Bloom 分類
Step 6: quality_flag 驗證
Step 7: 匯入 DB
```

### Step 2 LLM Prompt

```
System: 你是考題 PDF 結構化專家。

User:
以下是考試 PDF 的原始文字提取（包含頁首頁尾雜訊）。
請將它轉換為結構化 Markdown 格式的考題列表。

規則：
1. 移除所有頁首（年份、科目名、考試日期、「答案 題 目」、頁碼）
2. 每題格式固定為：
   ## 題號. 題幹完整文字
   - (A) 選項A
   - (B) 選項B
   - (C) 選項C
   - (D) 選項D
   **答案：X**
3. 跨頁的題目必須合併為完整的一題（題幹+4選項+答案）
4. 答案從文字中的「A/B/C/D 題號.」格式提取
5. 只輸出 Markdown，不要說明

原始文字：
{raw_pages_text}
```

### 批次策略

| 參數 | 值 | 理由 |
|------|---|------|
| 每批頁數 | 4-5 頁 | 控制 token 數（~2000 input token/頁） |
| LLM 模型 | Claude Sonnet | 平衡品質和成本 |
| max_tokens | 4096 | 每批約 15-20 題 |
| 單份 PDF 批次數 | 3-4 批（13 頁 PDF） | 序列執行，確保順序 |

### 成本估算

| 項目 | 計算 | 成本 |
|------|------|------|
| 單份 PDF（13 頁） | ~10K input + ~4K output token × 3 批 | ~$0.06 |
| 全部 68 份 PDF | 68 × $0.06 | **~$4.08** |
| 一次性投入 | | 在可接受範圍內 |

---

## 三、MD 格式規範

```markdown
# 114 年第四次 AI 應用規劃師-初級能力鑑定
## 第一科：人工智慧基礎概論

## 1. 在機器學習中，若要解決「手寫數字辨識」問題，最常使用下列哪一種學習方式？
- (A) 監督式學習（Supervised Learning）
- (B) 非監督式學習（Unsupervised Learning）
- (C) 強化式學習（Reinforcement Learning）
- (D) 自監督學習（Self-Supervised Learning）
**答案：A**

## 2. ...
```

### 必要欄位

- `## 題號.` — 題號（數字）
- 題幹 — 題號後的完整文字
- `- (A/B/C/D)` — 4 個選項
- `**答案：X**` — 正確答案字母

### 數學公式規範（KaTeX）

| 場景 | PDF 原始 | MD 輸出 |
|------|---------|--------|
| 上標 | `10 5`（上標丟失） | `$10^5$` |
| 下標 | `xi` | `$x_i$` |
| 分數 | `P/Q` | `$\frac{P}{Q}$` |
| 條件機率 | `P(A|B)` | `$P(A \| B)$` |
| 求和 | `Σ i=1 n` | `$\sum_{i=1}^{n}$` |
| 希臘字母 | `α, β, σ` | `$\alpha, \beta, \sigma$` |
| 程式碼 | `for i in range(10)` | `` `for i in range(10)` `` |

**LLM 的職責**：根據語意還原 PDF 提取時丟失的數學格式。
例如 `10 5` 在「數值量級約為 10 5」的語境下 → `$10^5$`。

**前端的職責**：已有 KaTeX 渲染支援（react-katex / remark-math）。
`questions.content` 中的 `$...$` 會被自動渲染為數學公式。

**DB 儲存**：`questions.content` 欄位 DBML 已標註 `note: '支援 Markdown + KaTeX'`。
KaTeX 語法直接存入，無需轉換。

---

## 四、MD → JSON 解析器（簡單 regex）

LLM 產出的 MD 格式統一後，解析變得極其簡單：

```python
def parse_md_to_questions(md_text: str) -> list[dict]:
    """從結構化 Markdown 提取題目"""
    questions = []
    # 用 "## 數字." 分割
    parts = re.split(r'## (\d+)\.\s*', md_text)

    for i in range(1, len(parts) - 1, 2):
        num = int(parts[i])
        raw = parts[i + 1].strip()

        # 提取答案
        answer_match = re.search(r'\*\*答案[：:]\s*([A-D])\*\*', raw)
        answer = answer_match.group(1) if answer_match else ""

        # 提取選項
        options = {}
        for letter in "ABCD":
            m = re.search(rf'- \({letter}\)\s*(.+?)(?=\n- \(|$|\n\*\*)', raw, re.DOTALL)
            if m:
                options[letter] = m.group(1).strip()

        # 題幹 = 選項之前的文字
        first_opt = re.search(r'\n- \(A\)', raw)
        content = raw[:first_opt.start()].strip() if first_opt else raw

        questions.append({
            "question_number": num,
            "content": content,
            "option_a": options.get("A", ""),
            "option_b": options.get("B", ""),
            "option_c": options.get("C", ""),
            "option_d": options.get("D", ""),
            "correct_answer": answer,
        })

    return questions
```

---

## 五、PoC 驗證結果（2026-04-03）

| 指標 | regex 解析器 | LLM → MD |
|------|-----------|----------|
| iPAS 4 頁（題 12-28） | 題幹截斷 6 題、選項溢出 3 題 | **17 題全部完整** |
| 跨頁合併 | ❌ 無法處理 | ✅ 自動合併 |
| 頁首清除 | ⚠️ regex 不穩定 | ✅ LLM 完美去除 |
| 答案提取 | ✅（答案在前格式） | ✅ |
| 成本 | $0 | ~$0.02/批 |

---

## 六、實作計畫

| 優先 | 項目 | 工期 |
|------|------|------|
| 1 | 建立 `exam-bank/parsers/llm_pdf_converter.py` | 1 天 |
| 2 | 對所有 68 份 PDF 執行 LLM 轉換 → MD 存檔 | 0.5 天 |
| 3 | 從 MD 解析為 JSON（簡單 regex） | 0.5 天 |
| 4 | Bloom 分類 + 品質驗證 + 匯入 DB | 0.5 天 |
| **合計** | | **~2.5 天** |

---

## 七、與現有模組的關係

```
exam-bank/
├── parsers/
│   ├── parse_exam_pdf.py          ← 舊 regex 解析器（保留為 fallback）
│   └── llm_pdf_converter.py       ← 新 LLM 轉換器（正式使用）
├── data/
│   ├── markdown/                   ← LLM 轉換後的 MD 檔（SSOT）
│   │   ├── ipas/ai_planner/114_fundamentals.md
│   │   └── ...
│   └── historical_questions/       ← JSON + PDF
└── docs/
    └── pdf-to-markdown-spec.md     ← 本文件
```

**MD 檔案是考題的 SSOT（唯一真實來源）**，JSON 和 DB 都從 MD 衍生。
