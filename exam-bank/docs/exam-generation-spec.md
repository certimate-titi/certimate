# TiTi 出題引擎設計規格書 v2.0

> **文件層級**：⭐考題設計人員最高設計原則
> **版本**：v2.0 | 2026-04-03
> **學術基礎**：`project/01_Management/07_學習科學技術白皮書.md`
> **OKR 對齊**：O1（最強 AI 出題引擎）、O3-KR3（弱點練習答對率提升 ≥ 15%）

---

## 一、四層出題 Pipeline 全景圖

```
┌──────────────────────────────────────────────────────────────┐
│ Layer -1：模式判定（Mode Selection）                          │
│ 距考天數 → 🔥衝刺 / 📚標準 / 🧠精熟                         │
│ 學術依據：#5 三模式動態任務 + Bjork 可期望困難理論            │
└─────────────────────────┬────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 0：弱點 + 記憶 + 信心度 綜合分析                        │
│ node_mastery（掌握度）+ question_stats（SM-2 ease_factor）   │
│ + 信心度四象限（危險盲點優先）+ 艾賓浩斯到期偵測              │
│ 學術依據：#1 艾賓浩斯 + #2 SM-2 + #6 後設認知 + #7 信心度    │
│ → 產出：每節點的綜合權重                                     │
└─────────────────────────┬────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 1：配比計算（Quota Allocation）                         │
│ 模式配比 × 弱點權重 × 使用者難度 × Bloom 目標                │
│ 學術依據：#3 Bloom 認知分類                                  │
│ → 產出：每節點的題數配額 + 難度分佈 + Bloom 目標              │
└─────────────────────────┬────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 2：混合式出題 + 交錯排列                                │
│ 20% 考古題 🟢 + 80% AI 生成 🟡                              │
│ → 交錯排列（A→B→C→A→B→C）+ 難度分散 + 開局保護              │
│ 學術依據：#4 交錯練習                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、Layer -1 — 模式判定

### 觸發規則

```python
exam_date = user.learning_journey.exam_date
days_left = (exam_date - today).days if exam_date else None

if days_left is not None and days_left <= 14:
    mode = "sprint"      # 🔥 衝刺模式
elif days_left is not None and days_left <= 180:
    mode = "standard"    # 📚 標準模式
else:
    mode = "mastery"     # 🧠 精熟模式（無考試日期或 > 6 個月）
```

### 三模式配比矩陣

| 模式 | 題目來源配比 | 弱點影響力 | Bloom 傾向 | 適用 |
|------|-----------|----------|-----------|------|
| 🔥 衝刺 | 錯題 50% / 新題 40% / 高頻考點 10% | 0.8（極高） | remember 30% + apply 30% | 距考 ≤ 14 天 |
| 📚 標準 | 新題 50% / 複習 30% / 弱點補強 20% | 0.6（中等） | 均衡 6 層次 | 1-6 個月 |
| 🧠 精熟 | 遺忘邊緣 70% / 跨章節 20% / 新題 10% | 0.4（低） | analyze 25% + evaluate 25% | > 6 月或無日期 |

---

## 三、Layer 0 — 弱點 + 記憶 + 信心度 綜合分析

### 資料來源

| 資料表 | 欄位 | 用途 |
|--------|------|------|
| `node_mastery` | mastery_rate, color | 考點掌握度（答對率） |
| `question_stats` | ease_factor, next_review_date, success_count, fail_count | SM-2 記憶衰退 |
| `answers` | confidence, is_correct | 信心度四象限 |

### 綜合權重計算

```python
for node in selected_nodes:
    mastery = query(node_mastery, user_id, node_id)
    stats = query(question_stats, user_id, node_id)

    # ── 維度 1：掌握度權重（越弱越高）──
    if not mastery or mastery.color == "gray":
        weakness = 0.5        # 未測 → 中等
    elif mastery.mastery_rate < 60:
        weakness = 0.8        # 🔴 弱點 → 高權重
    elif mastery.mastery_rate < 80:
        weakness = 0.5        # 🟠 部分 → 中等
    else:
        weakness = 0.2        # 🟢 精熟 → 低權重

    # ── 維度 2：SM-2 記憶緊迫度 ──
    if stats and stats.ease_factor < 2.0:
        memory_urgency = 0.3  # ease_factor 低 → 記憶不穩固
    elif stats and stats.next_review_date and stats.next_review_date <= today:
        memory_urgency = 0.2  # 到期需複習
    else:
        memory_urgency = 0.0  # 不急

    # ── 維度 3：信心度危險盲點 ──
    blindspot_count = count(answers WHERE
        node_id = node.id AND
        confidence = 'high' AND is_correct = false
    )
    confidence_weight = min(0.3, blindspot_count * 0.1)

    # ── 綜合 ──
    node.weight = weakness + memory_urgency + confidence_weight
    # 範圍: 0.2（精熟+無急迫+無盲點）~ 1.4（弱點+急迫+多盲點）
```

### 信心度四象限說明

```
              答對           答錯
確定  │ ✅ 真正掌握     │ 🔴 危險盲點    │ ← confidence_weight += 0.1/次
猜測  │ 🟡 幸運猜對     │ ⚪ 預期中弱點   │
```

- **危險盲點**（confident + wrong）：最高優先，ease_factor 額外 -0.2，複習間隔減半
- **幸運猜對**（guessing + correct）：仍排入複習，不因答對跳過

---

## 四、Layer 1 — 配比計算

### Step 1：按模式決定題目來源

```python
if mode == "sprint":
    # 衝刺：50% 從錯題表抽取
    wrong_pool = query(wrong_answers, user_id, subject_id)
    wrong_count = min(round(total_q * 0.5), len(wrong_pool))
    new_count = total_q - wrong_count

elif mode == "standard":
    # 標準：弱點加權分配新題 + 10% 錯題穿插
    wrong_count = round(total_q * 0.1)
    new_count = total_q - wrong_count

elif mode == "mastery":
    # 精熟：70% 從 SM-2 到期題目抽取
    review_pool = query(question_stats WHERE next_review_date <= today)
    review_count = min(round(total_q * 0.7), len(review_pool))
    new_count = total_q - review_count
```

### Step 2：按弱點權重分配每節點配額

```python
total_weight = sum(node.weight for node in nodes)
for node in nodes:
    node.quota = max(1, round(new_count * node.weight / total_weight))
# 調整確保 sum(quotas) == new_count
```

### Step 3：每節點內部的難度 × Bloom 雙維度

#### 難度分配（弱點覆寫使用者設定）

```python
# 使用者的 difficulty 設定是基線
base_diff = {
    1: {"easy": 60, "medium": 30, "hard": 10},
    2: {"easy": 30, "medium": 50, "hard": 20},
    3: {"easy": 10, "medium": 30, "hard": 60},
}[user_difficulty]

# 弱點覆寫（weakness_influence = mode 的弱點影響力）
weakness_adjusted = {
    "red":    {"easy": 50, "medium": 40, "hard": 10},  # 弱點：基礎鞏固
    "orange": {"easy": 20, "medium": 50, "hard": 30},  # 部分：均衡偏難
    "green":  {"easy": 10, "medium": 30, "hard": 60},  # 精熟：挑戰為主
    "gray":   base_diff,                                 # 未測：用使用者設定
}[node.mastery_color]

# 混合（弱點佔 mode.weakness_influence 權重）
wi = mode.weakness_influence  # 0.4~0.8
final_diff = {
    k: round(base_diff[k] * (1 - wi) + weakness_adjusted[k] * wi)
    for k in ["easy", "medium", "hard"]
}
```

#### Bloom 分佈目標

| 弱點狀態 | Bloom 傾向 | 理由 |
|---------|-----------|------|
| 🔴 弱點 | remember:40 understand:30 apply:20 analyze:10 | 先鞏固基本記憶和理解 |
| 🟠 部分 | remember:20 understand:20 apply:25 analyze:20 evaluate:10 create:5 | 從理解向應用過渡 |
| 🟢 精熟 | apply:20 analyze:25 evaluate:25 create:20 understand:10 | 挑戰高階思維 |
| ⬜ 未測 | 依 mode 的 bloom_bias | 依模式預設 |

**當科目有考古題 Bloom 統計時**：以考古題統計為基準，弱點微調在此基準上 ±10%。

---

## 五、Layer 2 — 混合式出題 + 交錯排列

### 混合策略

| 狀態 | 考古題 🟢 | AI 生成 🟡 | AI context |
|------|----------|-----------|-----------|
| 有考古題 + 有資料 | ~20% | ~80% | 考古題 few-shot + 上傳資料 RAG |
| 有考古題 + 無資料 | ~20% | ~80% | 考古題 few-shot + 節點名稱 |
| 無考古題 + 有資料 | 0% | 100% | 上傳資料 RAG |
| 無考古題 + 無資料 | — | — | ❌ 報錯「請上傳教材或選擇有題庫的科目」 |

### 考古題分層抽樣

```python
for node in nodes:
    hist_target = max(1, round(node.quota * 0.2))
    hist_pool = query(questions WHERE node_id AND historical_source IS NOT NULL)

    # 按難度分層
    for diff in ["easy", "medium", "hard"]:
        diff_count = round(hist_target * final_diff[diff] / 100)
        sampled = hist_pool.filter(difficulty=diff).order_by(random()).limit(diff_count)
        # 標記 reliability = "green"
```

### AI 生成 Prompt（考古題 few-shot）

```
System: 你是專業的 {科目} 出題老師。

以下是該科目的考古題範例（供參考出題風格和概念範圍）：
---
{3-5 題考古題完整內容}
---

{若有上傳資料} 以下是使用者的學習教材節選：
---
{RAG chunks}
---

請生成 {ai_target} 題新的選擇題：
- Bloom 目標分佈：{bloom_target}
- 難度分佈：{difficulty_target}
- 題目必須與考古題「相關但不重複」
- 每題 4 選項（A/B/C/D），標記正確答案字母
- 每題附 50 字以內的解析
```

### 交錯排列演算法

```python
def interleave_by_node(questions):
    """A→B→C→A→B→C 交錯排列"""
    by_node = defaultdict(deque)
    for q in questions:
        by_node[q.node_id].append(q)

    result = []
    node_order = list(by_node.keys())
    while any(by_node.values()):
        for nid in node_order:
            if by_node[nid]:
                result.append(by_node[nid].popleft())
    return result

def difficulty_smooth(questions):
    """避免連續 3 題以上相同難度"""
    # 若連續 3 題 hard → 插入 1 題 easy/medium
    ...

def ensure_easy_opening(questions, min_easy=1, first_n=3):
    """前 3 題保證至少 1 題 easy，建立正向開局"""
    easy_in_first = [q for q in questions[:first_n] if q.difficulty == "easy"]
    if len(easy_in_first) < min_easy:
        # 從後面找一題 easy 換到前 3
        ...
```

---

## 六、設計原則（6 大準則）

### 原則 1：學習科學驅動（Science-Driven）

所有出題邏輯必須追溯到白皮書 10 大學習科學中的至少 1 項。無學術依據的出題規則不得上線。

### 原則 2：弱點優先（Weakness-First）

出題配比的第一考量是使用者的弱點分析結果，而非平均分配。弱點節點最多可佔總題數 40%。

### 原則 3：混合信度（Hybrid Reliability）

每份考卷 20% 考古題（🟢）+ 80% AI（🟡）。純考古或純 AI 都不是最佳策略：考古題確保品質錨定，AI 確保題目多樣性。

### 原則 4：答案格式統一（Unified Format）

所有題目 `correct_answer` 統一為 `"A"/"B"/"C"/"D"` 字母格式。

### 原則 5：考點追溯（Node Traceability）

每道題目必須有 `node_id`，否則無法用於弱點分析、後設認知雷達。

### 原則 6：模式自適應（Mode-Adaptive）

出題配比不是靜態的——距考天數自動切換模式，不同模式的題目來源、難度、Bloom 分佈皆不同。

---

## 七、問題清單 v3（含白皮書對照）

### 已解決

| # | 問題 | 解決方式 |
|---|------|---------|
| P1 | Fallback 品質差 | 無 LLM+無資料 → 報錯 |
| P2 | 考古題不足 | 20/80 混合 |
| P5 | source_text 空 | 考古題 few-shot |
| P6 | 無信度標示 | 🟢/🟡 自動標記 |
| P7 | 無 Bloom 控制 | 分層抽樣 + bloom_bias |

### 需實作

| # | 問題 | 嚴重度 | 白皮書 | 負責 |
|---|------|--------|--------|------|
| P3 | AI 題無 node_id | 🟡 | #6 | 後端 |
| P4 | 答案格式不一致 | 🟡 | — | 後端 |
| P9 | 需要 LLM API key | 🔴 | — | 運營 |
| P10 | few-shot prompt | 🟡 | #3 | Prompt |
| **P12** | **三模式未實作** | 🔴 | **#5** | **後端+考題** |
| **P13** | **交錯排列未實作** | 🟡 | **#4** | **後端** |
| **P14** | **SM-2 未讀取** | 🟡 | **#2** | **後端** |
| **P15** | **到期複習偵測** | 🟡 | **#1** | **後端** |
| **P16** | **信心度未整合** | 🟡 | **#7** | **後端** |
| **P17** | **錯題穿插未實作** | 🟡 | **#5** | **後端** |
| **P18** | **開局保護未實作** | ⚠️ | **#4** | **後端** |

### 實作優先順序

| 優先 | 問題 | 預估工期 |
|------|------|---------|
| 1 | P9 LLM key 配置 | 0.5 天 |
| 2 | P12 三模式引擎 | 2 天 |
| 3 | P3+P4 node_id+答案統一 | 1 天 |
| 4 | P13+P18 交錯排列+開局保護 | 1 天 |
| 5 | P14+P15 SM-2+到期偵測 | 1.5 天 |
| 6 | P16 信心度整合 | 1 天 |
| 7 | P17 錯題穿插 | 0.5 天 |
| 8 | P10 few-shot prompt | 1 天 |
| **合計** | | **~8.5 天** |

---

## 八、API 契約（目標版）

### POST /exams/config（增加 mode 回傳）

```json
// Request（不變）
{
  "node_ids": ["uuid", ...],
  "question_count": 20,
  "difficulty": 2
}

// Response（新增 mode + analysis）
{
  "exam_id": "uuid",
  "total_questions": 20,
  "mode": "standard",
  "mode_reason": "距考 45 天，自動使用標準模式",
  "weakness_analysis": {
    "nodes": [
      {"node_id": "uuid", "name": "生成式AI", "mastery": 45, "color": "red", "weight": 1.1, "quota": 8},
      {"node_id": "uuid", "name": "基礎概論", "mastery": 85, "color": "green", "weight": 0.2, "quota": 2}
    ]
  }
}
```

### POST /exams/{id}/generate（回傳增加 composition）

```json
{
  "exam_id": "uuid",
  "exam": {"status": "READY", "total_questions": 20},
  "composition": {
    "historical_count": 4,
    "ai_count": 16,
    "wrong_review_count": 0,
    "bloom_actual": {"remember": 5, "understand": 4, "apply": 5, "analyze": 3, "evaluate": 2, "create": 1},
    "interleaving": true
  },
  "questions": [...]
}
```

---

## 九、相關 Feature 檔

| Feature | 涵蓋範圍 |
|---------|---------|
| `04-測驗設定.feature` | config、Bloom 配比、考古題節點選擇 |
| `04a-AI考題生成服務.feature` | 4 階段 AI Pipeline |
| `07-錯題複習與AI教練.feature` | 錯題穿插來源 |
| `09-學習記憶排程.feature` | SM-2 + 艾賓浩斯排程 |
| `18-題目分類與考試趨勢分析.feature` | Bloom 統計 |
| `19-交錯練習.feature` | 交錯排列 |
| `20-信心度校準.feature` | 四象限 + 危險盲點 |
| `23-考古題題庫管理.feature` | 匯入、抽題、信度 |

---

## 十、學習科學覆蓋度對照表

| # | 學習科學 | 出題 Pipeline 位置 | 狀態 |
|---|---------|-------------------|------|
| 1 | 艾賓浩斯間隔複習 | Layer 0 — 到期偵測 | 待實作 P15 |
| 2 | SM-2 自適應 | Layer 0 — ease_factor 讀取 | 待實作 P14 |
| 3 | Bloom 認知分類 | Layer 1 — bloom_bias | ⚠️ 部分 |
| 4 | 交錯練習 | Layer 2 — interleave_by_node | 待實作 P13 |
| 5 | 三模式動態 | Layer -1 — mode selection | 待實作 P12 |
| 6 | 後設認知雷達 | Layer 0 — weakness analysis | ⚠️ 部分 |
| 7 | 信心度校準 | Layer 0 — confidence_weight | 待實作 P16 |
| 8 | 蘇格拉底教練 | 不影響出題 | — |
| 9 | 遊戲化 | 不影響出題 | — |
| 10 | 番茄鐘 | 不影響出題 | — |

---

> **本文件為⭐考題設計人員進行任何出題相關修改的最高準則。**
> 所有修改必須符合 6 大設計原則，並可追溯到對應的學習科學理論和 Feature 檔。
