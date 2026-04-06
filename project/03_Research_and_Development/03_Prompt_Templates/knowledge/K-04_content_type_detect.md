---
id: "K-04"
name: "content_type_detect"
display_name: "內容類型偵測"
category: "knowledge"
model: "gemini-flash"
max_tokens: 32
temperature: 0.0
version: 1
feature_refs:
  - "02-資源上傳"
variables:
  - name: "text_sample"
    description: "文字樣本（前 500 字）"
    example: "第一條 本法所稱金融消費者保護..."
---

## System Prompt

```
判斷以下文字屬於哪種教育內容類型。
僅回覆 JSON，不要任何額外文字：
{{"type": "exam|regulation|textbook|summary|formula|syllabus|general"}}

類型說明：
- exam：考古題、模擬試題
- regulation：法規條文、辦法、準則
- textbook：教科書、講義、課本
- summary：筆記、摘要、重點整理
- formula：公式集、速查表
- syllabus：考試大綱、範圍說明
- general：其他一般性內容
```

## User Prompt

```
{text_sample}
```
