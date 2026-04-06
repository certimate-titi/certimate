---
id: "E-04"
name: "stage4_format_output"
display_name: "四階段 Pipeline：格式化輸出"
category: "exam"
model: "gemini-flash"
max_tokens: 4096
temperature: 0.0
version: 1
feature_refs:
  - "04a-AI考題生成服務"
variables:
  - name: "json_schema"
    description: "目標 JSON Schema"
    example: '{"exam_id": "string", "questions": [...]}'
  - name: "stage3_output"
    description: "階段 3 干擾項優化的 JSON 輸出"
    example: '[{"question_text": "...", "options": [...]}]'
---

## System Prompt

```
將以下考題轉換為嚴格的 JSON Schema 格式。
不增刪任何內容，僅做格式轉換與驗證。

目標 Schema：
{{
  "exam_id": "string（UUID）",
  "total_questions": "int",
  "questions": [
    {{
      "id": "string（UUID）",
      "text": "題幹文字",
      "options": ["選項A", "選項B", "選項C", "選項D"],
      "answer": "int（正確答案索引 0-3）",
      "difficulty": "easy|medium|hard",
      "bloom_level": "remember|understand|apply|analyze|evaluate|create",
      "exam_point": "考點名稱",
      "reliable": "historical|ai_generated|low_material",
      "explanation": "詳細解析文字",
      "distractor_reasons": {{
        "1": "錯誤原因",
        "2": "錯誤原因",
        "3": "錯誤原因"
      }}
    }}
  ]
}}

驗證規則：
1. 每題必須恰好 4 個選項
2. answer 必須為 0-3 的整數
3. 所有必要欄位不可為 null
4. JSON 必須可被 json.loads() 正確解析
```

## User Prompt

```
完整考題（階段 3 輸出）：
{stage3_output}
```
