#!/usr/bin/env python3
"""Lint backend/tests/features/steps/__init__.py — every `from .X import Y`
must point to an actually-existing file or package on disk.

Catches the class of bug where a commit references a step module that was
never `git add`ed (occurred on 2026-04-18, blocking all behave runs for 19 days).

Run from repo root or backend/. Exits 1 on any missing target.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

INIT_PATH = Path("tests/features/steps/__init__.py")
if not INIT_PATH.exists():
    INIT_PATH = Path("backend/tests/features/steps/__init__.py")
if not INIT_PATH.exists():
    print(f"[lint_step_imports] cannot find {INIT_PATH}", file=sys.stderr)
    sys.exit(2)

PATTERN = re.compile(r"^\s*from\s+\.([\w.]+)\s+import\s+", re.MULTILINE)
violations: list[str] = []
base = INIT_PATH.parent  # tests/features/steps/

for match in PATTERN.finditer(INIT_PATH.read_text(encoding="utf-8")):
    rel = match.group(1)
    # `from .foo.bar import X` resolves if any of these exist:
    #   tests/features/steps/foo/bar.py            (module)
    #   tests/features/steps/foo/bar/__init__.py   (regular package)
    #   tests/features/steps/foo/bar/              (PEP 420 namespace package)
    candidate_module = base / Path(*rel.split(".")).with_suffix(".py")
    candidate_pkg = base / Path(*rel.split(".")) / "__init__.py"
    candidate_dir = base / Path(*rel.split("."))
    if (
        not candidate_module.exists()
        and not candidate_pkg.exists()
        and not candidate_dir.is_dir()
    ):
        line = INIT_PATH.read_text().count("\n", 0, match.start()) + 1
        violations.append(f"{INIT_PATH}:{line}: missing target for `from .{rel} import ...`")

if violations:
    print("Step import lint failed:")
    for v in violations:
        print(f"  {v}")
    sys.exit(1)

print(f"[lint_step_imports] OK — all `from .X import` targets exist in {base}")
