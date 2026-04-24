#!/usr/bin/env python3
"""試驗：強化 prompt 讓 Haiku 抽取 PDF 內的圖表內容。

目標：驗證 iPAS ML Q50（matplotlib 圖表題）能否從圖中抽到可判讀的資訊。
"""
import json
import subprocess
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent.parent
MODEL = "claude-sonnet-4-6"
PDF = BACKEND / "data/historical_questions/ipas/ai_planner/114_ai_mid_ml.pdf"

PROMPT = """請使用 Read 工具讀取以下 PDF，逐題抽取成結構化 JSON。

輸出格式必須是 JSON 陣列，每題一個 object：
[
  {
    "question_number": 50,
    "content": "題幹完整文字（含圖表描述）",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A/B/C/D 或 空字串",
    "source_snippet": "前 40 字原文",
    "has_figure": true/false,
    "figure_description": "若題目含圖/表/圖片，詳細描述圖內容（座標軸標題、刻度、資料趨勢、線條顏色、關鍵數值等），否則空字串"
  }
]

重要規則：
1. **只抽第 50 題**（Q50），其他題目忽略
2. **圖表處理**：Q50 含 matplotlib 圖，請仔細觀察 PDF 內嵌圖像，詳細描述圖內容：
   - 圖的類型（折線圖、散佈圖、熱力圖等）
   - X/Y 軸標題與刻度範圍
   - 每條線/點的顏色、標籤（label，例如 'train_loss'、'val_accuracy'）
   - 曲線趨勢（上升/下降/震盪/收斂）與關鍵轉折點
   - 若有多條線，描述它們的相對位置（誰高誰低、是否交叉）
3. 若圖真的看不清或 PDF 無圖，has_figure 填 false、figure_description 空字串
4. 忠實抽取題幹、選項，不改寫
5. correct_answer 若 PDF 內無明確答案則留空字串
6. 只輸出 JSON 陣列，不要 markdown、不要說明

PDF 路徑：__PDF_PATH__"""


def main():
    cmd = [
        "claude", "-p", PROMPT.replace("__PDF_PATH__", str(PDF.resolve())),
        "--model", MODEL,
        "--allowedTools", "Read",
        "--output-format", "text",
    ]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    print(f"耗時 {time.time()-t0:.1f}s, stderr: {r.stderr[:200]}")
    raw = r.stdout.strip()
    if raw.startswith("```"):
        lines = [l for l in raw.split("\n") if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()

    print(f"\n原始輸出（{len(raw)} chars）：")
    print(raw[:3000])

    try:
        data = json.loads(raw)
        print("\n" + "=" * 60)
        print("解析結果")
        print("=" * 60)
        for q in data:
            print(f"\n題號：{q.get('question_number')}")
            print(f"has_figure: {q.get('has_figure')}")
            print(f"figure_description: {q.get('figure_description', '')[:500]}")
            print(f"content (前 300): {q.get('content', '')[:300]}")
            print(f"答案: {q.get('correct_answer')}")
            print("選項：")
            for k in ['a','b','c','d']:
                print(f"  {k.upper()}: {q.get(f'option_{k}', '')[:100]}")
    except json.JSONDecodeError as e:
        print(f"JSON parse 失敗：{e}")


if __name__ == "__main__":
    main()
