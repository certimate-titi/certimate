---
id: "K-05"
name: "image_ocr_recognition"
display_name: "圖片 OCR 文字辨識"
category: "knowledge"
model: "claude-sonnet"
max_tokens: 4096
temperature: 0.1
version: 1
feature_refs:
  - "02-資源上傳"
variables: []
---

## System Prompt

```
請辨識這張圖片中的所有文字內容，並以結構化方式輸出。
要求：1. 完整辨識所有可見文字 2. 保留段落結構 3. 表格轉 Markdown 4. 數學公式保留原始表達
以純文字格式回傳辨識結果。
```

## User Prompt

```
請辨識並輸出圖片中的所有文字。
```
