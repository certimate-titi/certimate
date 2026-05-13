"""Markdown hashtag parser utility — Feature 52 筆記 hashtag 系統。

Obsidian-style hashtag 解析：
  `#word`（前面是空白或行首，# 後無空格）= tag
  `# Heading`（# 後有空格）= markdown heading，不算 tag

Regex: (?:(?<=\\s)|(?:^|(?<=\\n)))#([a-zA-Z0-9_\\-一-鿿]+)
支援：英數字、底線、連字號、CJK 字元（含繁體/簡體/日文漢字）

Unicode 範圍說明：
  一-鿿 = U+4E00–U+9FFF（CJK 基本漢字）
"""

import re

# Hashtag regex：
# (?:(?<=\s)|(?:^|(?<=\n))) — 前面是空白、行首、或換行後的行首
# # — 井字號
# ([a-zA-Z0-9_\-一-鿿]+) — tag 內容（不含空格，支援英數/底線/連字號/CJK）
HASHTAG_RE = re.compile(
    r"(?:(?<=\s)|(?:^|(?<=\n)))#([a-zA-Z0-9_\-一-鿿]+)",
    re.MULTILINE,
)


def extract_hashtags(content: str) -> list[tuple[str, str]]:
    """從 markdown 內容抽取 hashtag。

    規則：
    - `#word`（前面是空白/行首）→ tag
    - `# Heading`（# 後有空格）→ markdown heading，忽略
    - case-insensitive normalization：`#AI` 和 `#ai` → normalized=ai
    - 去重：同一 normalized 只保留第一次出現的 display 原文

    Args:
        content: markdown 文字內容

    Returns:
        [(normalized, display), ...] — 去重後的 tag 列表，保留首次出現原文。
        例：[("深度學習", "深度學習"), ("ai", "AI"), ("dl-101", "dl-101")]
    """
    seen: set[str] = set()
    out: list[tuple[str, str]] = []

    for m in HASHTAG_RE.finditer(content):
        raw = m.group(1)
        normalized = raw.lower().strip()
        if not normalized:
            continue
        if normalized not in seen:
            seen.add(normalized)
            out.append((normalized, raw))

    return out
