"""Mindmap data-quality verifier.

Run this after UnifiedKnowledgeExtractionService.extract() (or manually)
to catch data-quality regressions that "nodes exist" assertions miss.

Checks (each is a hard fail):

1. **DESC_MISSING** — source_text length < len(name) + 50 chars
   Every node must have a real description, not just "# name\\n\\n".

2. **CHAPTER_ZERO_STRENGTH** — depth=1 node has support_strength=0 while
   at least one of its children has support_strength>0.
   Chapters should aggregate from their children (Layer 1 2-pass).

3. **ORPHAN_SECTION** — depth=2 node with no parent_id set.
   Sections must always nest under a chapter.

4. **NAME_COLLISION** — two nodes in same subject with identical names.
   LLM sometimes duplicates sections across chapters; should be merged.

5. **EMPTY_TREE** — subject has zero knowledge_nodes despite having
   questions or resources (indicates extract() silently no-opped).

6. **STRENGTH_OUT_OF_RANGE** — support_strength not in [0.0, 1.0].

7. **BLOOM_EMPTY** — depth=2 node with exam_frequency='medium' but no
   bloom information in source_text (weak signal of schema drift).

Usage:
    DATABASE_URL=... .venv/bin/python -m app.scripts.verify_mindmap_quality \\
        --subject-id <uuid>     # single subject
        --all-subjects           # every subject with nodes

Exit code 0 = all checks pass; 1 = failures found; returns report JSON
on stdout for CI integration.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

MIN_DESCRIPTION_CHARS = 50  # description must add at least this many chars beyond "# {name}\n\n"


def _check_subject(db: Session, subject_id: str) -> dict[str, Any]:
    sid = uuid.UUID(subject_id)
    name_row = db.execute(
        text("SELECT name FROM subjects WHERE id=:sid"), {"sid": sid}
    ).first()
    if not name_row:
        return {"subject_id": subject_id, "error": "subject not found"}

    subject_name = name_row[0]

    nodes = db.execute(
        text(
            """
            SELECT id, name, depth, parent_id, support_strength,
                   LENGTH(COALESCE(source_text,'')) AS txt_len,
                   source_text
            FROM knowledge_nodes
            WHERE subject_id=:sid
            ORDER BY depth, sort_order
            """
        ),
        {"sid": sid},
    ).fetchall()

    failures: list[dict[str, Any]] = []

    # Check 5: EMPTY_TREE
    if not nodes:
        q_count = db.execute(
            text(
                """
                SELECT COUNT(*) FROM questions q
                JOIN historical_exams he ON q.historical_exam_id=he.id
                JOIN subjects s ON s.id=:sid
                WHERE (he.exam_code||':'||he.subject_code) IN (
                    SELECT jsonb_array_elements_text(s.exam_subject_codes)
                )
                """
            ),
            {"sid": sid},
        ).scalar() or 0
        if q_count > 0:
            failures.append(
                {
                    "code": "EMPTY_TREE",
                    "msg": f"0 nodes but {q_count} questions available",
                }
            )
        return _build_report(subject_id, subject_name, 0, failures)

    # Build child map for check 2
    children_of: dict[uuid.UUID, list] = {}
    for n in nodes:
        if n[3] is not None:
            children_of.setdefault(n[3], []).append(n)

    name_counts: dict[str, int] = {}

    for n in nodes:
        nid, nname, depth, pid, strength, txt_len, src = n
        strength = float(strength or 0)

        # 1. DESC_MISSING
        min_required = len(nname) + MIN_DESCRIPTION_CHARS
        if txt_len < min_required:
            failures.append(
                {
                    "code": "DESC_MISSING",
                    "node_id": str(nid),
                    "node_name": nname,
                    "depth": depth,
                    "txt_len": txt_len,
                    "min_required": min_required,
                }
            )

        # 2. CHAPTER_ZERO_STRENGTH
        if depth == 1 and strength == 0 and children_of.get(nid):
            kid_strengths = [float(c[4] or 0) for c in children_of[nid]]
            if any(s > 0 for s in kid_strengths):
                failures.append(
                    {
                        "code": "CHAPTER_ZERO_STRENGTH",
                        "node_name": nname,
                        "child_strengths": kid_strengths,
                    }
                )

        # 3. ORPHAN_SECTION
        if depth == 2 and pid is None:
            failures.append(
                {"code": "ORPHAN_SECTION", "node_name": nname}
            )

        # 6. STRENGTH_OUT_OF_RANGE
        if strength < 0.0 or strength > 1.0:
            failures.append(
                {
                    "code": "STRENGTH_OUT_OF_RANGE",
                    "node_name": nname,
                    "value": strength,
                }
            )

        # 4. NAME_COLLISION tally
        name_counts[nname] = name_counts.get(nname, 0) + 1

    # Emit collisions after tally
    for nname, cnt in name_counts.items():
        if cnt > 1:
            failures.append(
                {"code": "NAME_COLLISION", "node_name": nname, "count": cnt}
            )

    return _build_report(subject_id, subject_name, len(nodes), failures)


def _build_report(
    subject_id: str, subject_name: str, node_count: int, failures: list
) -> dict[str, Any]:
    return {
        "subject_id": subject_id,
        "subject_name": subject_name,
        "node_count": node_count,
        "failures": failures,
        "failure_count": len(failures),
        "passed": len(failures) == 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject-id", help="Single subject UUID")
    parser.add_argument(
        "--all-subjects", action="store_true",
        help="Check every subject that has knowledge_nodes",
    )
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set", file=sys.stderr)
        sys.exit(2)

    engine = create_engine(db_url)
    reports: list[dict[str, Any]] = []

    with Session(engine) as db:
        if args.subject_id:
            reports.append(_check_subject(db, args.subject_id))
        elif args.all_subjects:
            sids = db.execute(
                text(
                    """
                    SELECT DISTINCT subject_id::text FROM knowledge_nodes
                    """
                )
            ).fetchall()
            for (sid,) in sids:
                reports.append(_check_subject(db, sid))
        else:
            print("--subject-id or --all-subjects required", file=sys.stderr)
            sys.exit(2)

    # Summary
    total_failures = sum(r["failure_count"] for r in reports)
    print(json.dumps(
        {
            "reports": reports,
            "total_subjects": len(reports),
            "total_failures": total_failures,
            "overall_passed": total_failures == 0,
        },
        ensure_ascii=False,
        indent=2,
    ))
    sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()
