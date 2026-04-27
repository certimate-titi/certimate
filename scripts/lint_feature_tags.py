#!/usr/bin/env python3
"""BDD Feature Tag 分類規範 lint。

規則見 docs/bdd/tag-conventions.md。檢查：
1. backend/tests/features/ 內禁含 @frontend
2. project/features/ 內禁含 @backend
3. 同 Scenario 同時 @backend + @frontend → 應改為 @fullstack
4. 未標 tag 的 Scenario 以資料夾推斷預設並 warning
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend" / "tests" / "features"
PROJECT_DIR = ROOT / "project" / "features"

CLASS_TAGS = {"@backend", "@frontend", "@fullstack"}
TAG_LINE = re.compile(r"^\s*(@[\w\-:]+(?:\s+@[\w\-:]+)*)\s*$")
HEADING = re.compile(r"^\s*(Feature|Rule|Scenario|Scenario Outline|Example):", re.IGNORECASE)


def parse(path: Path):
    """Yield (lineno, kind, tags_set) for each Feature/Rule/Scenario heading."""
    pending: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            stripped = line.rstrip("\n")
            m_tag = TAG_LINE.match(stripped)
            if m_tag and not stripped.lstrip().startswith("#"):
                pending.update(m_tag.group(1).split())
                continue
            m_head = HEADING.match(stripped)
            if m_head:
                yield i, m_head.group(1).lower(), set(pending)
                pending = set()
                continue
            if stripped.strip() == "" or stripped.lstrip().startswith("#"):
                continue
            pending = set()


def class_tag_of(tags: set[str]) -> set[str]:
    return tags & CLASS_TAGS


def lint_dir(directory: Path, allowed: set[str], expected_default: str):
    issues: list[str] = []
    warnings: list[str] = []
    if not directory.exists():
        return issues, warnings
    for feature in sorted(directory.glob("*.feature")):
        feature_tags: set[str] = set()
        rule_tags: set[str] = set()
        for lineno, kind, tags in parse(feature):
            if kind == "feature":
                feature_tags = tags
                rule_tags = set()
            elif kind == "rule":
                rule_tags = tags
            else:
                effective = class_tag_of(tags) or class_tag_of(rule_tags) or class_tag_of(feature_tags)
                forbidden = (tags | rule_tags | feature_tags) & (CLASS_TAGS - allowed - {"@fullstack"})
                if forbidden:
                    issues.append(
                        f"{feature.relative_to(ROOT)}:{lineno}  Scenario 帶不允許的 tag {forbidden}（此資料夾僅允許 {allowed}）"
                    )
                if "@backend" in effective and "@frontend" in effective:
                    issues.append(
                        f"{feature.relative_to(ROOT)}:{lineno}  Scenario 同時帶 @backend 與 @frontend（請改為 @fullstack 或拆 Scenario）"
                    )
                if not effective:
                    warnings.append(
                        f"{feature.relative_to(ROOT)}:{lineno}  Scenario 未標 tag，預設視為 {expected_default}"
                    )
    return issues, warnings


def main() -> int:
    bk_issues, bk_warn = lint_dir(BACKEND_DIR, allowed={"@backend", "@fullstack"}, expected_default="@backend")
    pj_issues, pj_warn = lint_dir(PROJECT_DIR, allowed={"@frontend", "@fullstack"}, expected_default="@frontend")

    issues = bk_issues + pj_issues
    warnings = bk_warn + pj_warn

    if warnings:
        print(f"⚠️  {len(warnings)} warning（未標 tag，將以資料夾推斷）")
        for w in warnings[:20]:
            print(f"  {w}")
        if len(warnings) > 20:
            print(f"  ... 另 {len(warnings) - 20} 筆已省略")

    if issues:
        print(f"\n❌ {len(issues)} 違規")
        for it in issues:
            print(f"  {it}")
        return 1

    print(f"\n✅ Tag 分類規範通過（{len(warnings)} 過渡期 warning）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
