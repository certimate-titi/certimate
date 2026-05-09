"""K-ORPHAN-01 Prompt 模板 — AI 補洞鷹架生成.

用於從考古題反推 orphan 知識節點的學習鷹架。
輸出嚴格遵循 JSON Schema，供後處理做 fail-safe 校驗。

模板名稱：K-ORPHAN-01
設計規範：docs/design/orphan-mitigation-design.md 區塊 A.2
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
你是一位專業的證照考試教育顧問，精通從考古題反推知識定義。
你的任務是根據提供的考古題線索，為「{node_name}」這個知識節點生成一份學習鷹架。

## 嚴格限制（違反任一條即為無效輸出）

1. **禁止憑空發明**：所有術語、定義、範例必須有對應考古題依據，不得自行創作原文不存在的概念。
2. **禁止外部 URL**：輸出中絕對不能出現任何 http://、https://、www. 等外部連結或引用網址。
3. **字數嚴格限制**：
   - definition：≤ 120 字（中文字數計算）
   - illustration：≤ 200 字
   - practice_question.stem + options 合計：≤ 150 字
   - practice_question.explanation：≤ 100 字
4. **引用格式**：每個關鍵術語後必須標 [考古題#題號]，範例改編自考古題須標（改編自 {年份} 第 {X} 題）。
5. **不得包含完整原始考古題文字**（著作權風險）。
6. **輸出格式**：嚴格按下方 JSON Schema，不加任何額外說明或 markdown 包裝。

## 輸出 JSON Schema

```json
{
  "definition": "string（≤120字，一段話，無條列，引用考古題術語標 [考古題#題號]）",
  "illustration": "string（≤200字，一個具體情境或計算範例，若改編自考古題標（改編自{年份}第{X}題））",
  "practice_question": {
    "stem": "string（題目本身）",
    "options": ["A. 選項文字", "B. 選項文字", "C. 選項文字", "D. 選項文字"],
    "answer": "A|B|C|D",
    "explanation": "string（≤100字，聚焦「為什麼正確答案對、其他選項錯」）",
    "difficulty": "T1|T2|T3"
  }
}
```
"""

USER_PROMPT_TEMPLATE = """\
## 知識節點資訊

- **節點名稱**：{node_name}
- **父節點（章名）**：{parent_node_name}
- **科目**：{subject_name}

## 佐證考古題（共 {evidence_count} 題，以下為題幹摘要）

{evidence_stems}

---

請根據上方考古題線索，為「{node_name}」生成一份 K-ORPHAN-01 格式的學習鷹架。
嚴格遵守 System Prompt 的所有限制，直接輸出 JSON，不加任何前置說明。
"""


def build_system_prompt(node_name: str) -> str:
    """組合 system prompt，注入節點名稱。"""
    return SYSTEM_PROMPT.replace("{node_name}", node_name)


def build_user_prompt(
    node_name: str,
    parent_node_name: str,
    subject_name: str,
    evidence_stems: list[str],
) -> str:
    """組合 user prompt。

    Args:
        node_name: 知識節點名稱
        parent_node_name: 父節點（章名）
        subject_name: 科目名稱
        evidence_stems: 佐證考古題題幹列表（最多 8 題，每題前綴 [考古題#題號]）

    Returns:
        格式化後的 user prompt 字串
    """
    stems_text = "\n".join(
        f"{i + 1}. {stem}" for i, stem in enumerate(evidence_stems[:8])
    )
    return USER_PROMPT_TEMPLATE.format(
        node_name=node_name,
        parent_node_name=parent_node_name or "（無父節點）",
        subject_name=subject_name,
        evidence_count=len(evidence_stems[:8]),
        evidence_stems=stems_text,
    )
