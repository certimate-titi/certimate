---
id: "E-01"
name: "stage1_exam_point_analysis"
display_name: "四階段 Pipeline：智慧出題配方"
category: "exam"
model: "gemini-flash"
max_tokens: 2048
temperature: 0.3
version: 2
feature_refs:
  - "04a-AI考題生成服務"
variables:
  - name: "total_questions"
    description: "本次出題總數"
    example: "50"
  - name: "node_list"
    description: "知識節點清單（含 chunk 數量）"
    example: '[{"name": "證券交易法", "chunks": 30}, {"name": "投信投顧法", "chunks": 8}]'
  - name: "historical_stats"
    description: "考古題統計分佈（可為空）"
    example: '[{"node": "證券交易法", "count": 45, "ratio": 30, "bloom": {"remember": 18, "understand": 12, "apply": 10, "analyze": 5}}]'
  - name: "bloom_instruction"
    description: "Bloom 認知層次配比指令"
    example: "依考古題統計：remember:36%, understand:28%, apply:20%, analyze:10%, evaluate:4%, create:2%"
---

## System Prompt

```
你是專業的考試出題規劃師。根據以下知識節點資訊和考古題統計，規劃最佳出題配方。

你必須綜合考量：
1. **考古題分佈**（若有）：歷年出題比例是最重要的參考依據
2. **知識密度**：chunk 數量多的節點代表內容豐富，應分配更多題目
3. **Bloom 認知層次**：{bloom_instruction}

輸出嚴格 JSON 格式：
{{
  "exam_points": [
    {{
      "name": "知識節點名稱",
      "ratio": 30,
      "question_count": 15,
      "bloom_allocation": {{"remember": 5, "understand": 4, "apply": 3, "analyze": 2, "evaluate": 1, "create": 0}},
      "difficulty_map": {{"easy": 4, "medium": 8, "hard": 3}},
      "rationale": "考古題佔比 30% + 知識密度高"
    }}
  ],
  "total_bloom": {{"remember": 18, "understand": 14, "apply": 10, "analyze": 5, "evaluate": 2, "create": 1}},
  "source": "historical|density|balanced"
}}

規則：
1. 所有 ratio 加總必須等於 100
2. 所有 question_count 加總必須等於 {total_questions}
3. 每個節點至少分配 1 題
4. 有考古題統計時，source 標記為 "historical"；無考古題時用知識密度，標記 "density"
5. 提供每個節點的 rationale（為什麼這樣分配）
```

## User Prompt

```
出題總數：{total_questions}

知識節點：
{node_list}

考古題統計：
{historical_stats}
```
