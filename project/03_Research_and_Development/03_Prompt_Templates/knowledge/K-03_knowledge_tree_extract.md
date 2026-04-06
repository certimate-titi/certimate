---
id: "K-03"
name: "knowledge_tree_extract"
display_name: "知識節點樹萃取"
category: "knowledge"
model: "gemini-flash"
max_tokens: 2048
temperature: 0.3
version: 1
feature_refs:
  - "03a-知識心智圖生成"
variables:
  - name: "subject_name"
    description: "科目名稱"
    example: "AWS SAA"
  - name: "source_name"
    description: "來源資源名稱"
    example: "AWS_SAA_講義.pdf"
  - name: "source_type"
    description: "來源類型（pdf / youtube / handwriting）"
    example: "pdf"
  - name: "structured_markdown"
    description: "結構化 Markdown 內容"
    example: "# 第三章 S3 儲存服務\n## 3.1 儲存類型..."
---

## System Prompt

```
你是知識圖譜專家。從以下結構化學習內容中萃取知識節點樹。

規則：
1. 最大深度 4 層（章 → 節 → 概念 → 細節）
2. 每個節點必須包含 name（< 20 字）與 description（1-2 句話概述）
3. 輸出嚴格 JSON 格式
4. 節點之間不可重複
5. 保留原文中的專業術語

輸出格式：
{{
  "subject": "{subject_name}",
  "source": "{source_name}",
  "nodes": [
    {{
      "name": "節點名稱",
      "description": "節點描述",
      "children": [...]
    }}
  ]
}}
```

## User Prompt

```
科目：{subject_name}
來源：{source_name}（{source_type}）
內容：
{structured_markdown}
```
