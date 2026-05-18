#!/usr/bin/env python3
"""Backfill：平衡 resources.parsed_markdown 內未配對的 ``` code fence。

2026-05-19：AI 生成的 markdown 偶爾遺漏結尾 ```，導致前端 react-markdown
把後續整段（含表格）誤判為 code block。前端已加 render-time `balanceCodeFences`
兜底（components/MathContent.tsx），但 DB 內存的 source markdown 仍是壞的，
影響：
- 之後要匯出 / 換 viewer
- 餵給其他 LLM 做下游處理
- 任何不走 MathContent 的渲染路徑

此腳本對既有 ``resources.parsed_markdown`` 做一次性掃描 + 修補。

用法：
    # Dry-run（只統計奇數 fence 的列數）
    .venv/bin/python -m app.scripts.backfill_balance_code_fences --dry-run

    # 實際更新
    .venv/bin/python -m app.scripts.backfill_balance_code_fences

    # 限制處理筆數
    .venv/bin/python -m app.scripts.backfill_balance_code_fences --limit 500

設計：
- 與前端 ``balanceCodeFences`` 邏輯一致：行首 ``` 計數，奇數 → 尾端補 ```
- 已平衡 / 無 fence 的列不動，跳過（不改 ``updated_at`` 避免污染）
- 每筆 commit；中斷可續跑（再跑會 idempotent）
"""

import argparse
import logging
import re
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^\s*```", re.MULTILINE)


def needs_balance(md: str) -> bool:
    """偵測 ``` 是否奇數（未配對）。"""
    if not md:
        return False
    return len(_FENCE_RE.findall(md)) % 2 == 1


def balance(md: str) -> str:
    """補上結尾 ```（與前端 MathContent.balanceCodeFences 邏輯一致）。"""
    if md.endswith("\n"):
        return md + "```\n"
    return md + "\n```\n"


def run(dry_run: bool, limit: int | None) -> int:
    """掃描 resources 表並修補未配對的 fence；回傳 exit code。"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()

    try:
        # 只撈有 parsed_markdown 的列；用 LIKE 預過濾減少傳輸量（含至少一個 ```）
        sql = text(
            """
            SELECT id, parsed_markdown
            FROM resources
            WHERE parsed_markdown IS NOT NULL
              AND parsed_markdown LIKE '%```%'
            ORDER BY created_at DESC
            """
            + ("LIMIT :lim" if limit else "")
        )
        rows = db.execute(sql, {"lim": limit} if limit else {}).fetchall()
        log.info("掃描 %d 筆含 ``` 的 resources.parsed_markdown", len(rows))

        scanned = 0
        unbalanced = 0
        fixed = 0

        for row in rows:
            scanned += 1
            md = row.parsed_markdown
            if not needs_balance(md):
                continue
            unbalanced += 1
            if dry_run:
                continue
            new_md = balance(md)
            db.execute(
                text("UPDATE resources SET parsed_markdown = :md WHERE id = :id"),
                {"md": new_md, "id": row.id},
            )
            db.commit()
            fixed += 1
            log.info("  ✓ fixed %s (原 %d chars → %d)", row.id, len(md), len(new_md))

        log.info("=== 完成 ===")
        log.info("掃描：%d 筆", scanned)
        log.info("未配對 fence：%d 筆", unbalanced)
        if dry_run:
            log.info("Dry-run：未變更 DB（移除 --dry-run 實際執行）")
        else:
            log.info("已修補：%d 筆", fixed)
        return 0
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="只統計，不寫 DB")
    parser.add_argument("--limit", type=int, help="限制處理筆數（避免一次掃太多）")
    args = parser.parse_args()
    return run(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
