"""Given K-06 LLM mock scaffolds — Feature 38 pitfall persist BDD。"""

from behave import given


@given('K-06 v5 解析回傳 scaffolds 含一筆 type=pitfall')
def step_k06_returns_one_pitfall(context):
    """準備 1 筆 pitfall scaffold 給 _persist_parsed 處理。"""
    context.memo["parsed_scaffolds"] = [
        {
            "chapter_heading": "3.1 折現率",
            "type": "pitfall",
            "content": "⚠ 常見誤解：折現率 ≠ 通膨率，兩者基準不同。",
        }
    ]


@given(
    'K-06 v5 LLM 回傳 4 筆 scaffolds，其中 2 筆 (chapter=\'{chapter}\', type=pitfall)'
)
def step_k06_returns_duplicate_pitfalls(context, chapter):
    """準備 4 筆 scaffold，含 2 筆同章節 pitfall（測 dedup）。"""
    context.memo["parsed_scaffolds"] = [
        {
            "chapter_heading": chapter,
            "type": "pitfall",
            "content": "⚠ 迷思一：折現率與利率混淆。",
        },
        {
            "chapter_heading": chapter,
            "type": "pitfall",
            "content": "⚠ 迷思二：忽略時間複利效應。",
        },
        {
            "chapter_heading": chapter,
            "type": "takeaway",
            "content": "• 折現率 = 風險報酬率 + 無風險利率",
        },
        {
            "chapter_heading": "3.2 NPV",
            "type": "pitfall",
            "content": "⚠ NPV 折現基準應一致。",
        },
    ]
    context.memo["dedup_chapter"] = chapter
