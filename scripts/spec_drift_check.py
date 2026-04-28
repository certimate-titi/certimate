#!/usr/bin/env python3
"""Spec drift / deprecated feature 殘留巡檢。

讀取 `.titi/deprecated_features.json`（list of {key, prd, removed_at, reason}），
對 frontend/backend/project/features 全文 grep，發現殘留即報 violation。

CI 上跑：bash CI_FAIL_ON_DRIFT=1 python3 scripts/spec_drift_check.py
本地跑：python3 scripts/spec_drift_check.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEPRECATED_FILE = ROOT / ".titi" / "deprecated_features.json"

# Grep 範圍（白名單，避免掃 node_modules / .git / 已歷史化的 deliverables）
SEARCH_PATHS = [
    "frontend/app",
    "frontend/components",
    "frontend/lib",
    "frontend/hooks",
    "backend/app",
    "project/features",
]

# 排除路徑（含合理引用：release note、git history、本巡檢腳本本身）
EXCLUDE_PATTERNS = [
    "*.md",                          # docs / release notes 不視為違規
    "*deliverables*",                # CTO/CEO 簽核紀錄保留
    "*spec_drift_check*",            # 本腳本自身
    "*__pycache__*",
    "*node_modules*",
    "*.next*",
    "*test*",                        # 測試檔可能含 deprecated 關鍵字作 negative case
]


def load_deprecated() -> list[dict]:
    """讀 deprecated_features.json；無則回空清單（不算錯）。"""
    if not DEPRECATED_FILE.exists():
        return []
    try:
        return json.loads(DEPRECATED_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ Cannot parse {DEPRECATED_FILE}: {e}", file=sys.stderr)
        return []


def grep_keyword(keyword: str) -> list[str]:
    """於 SEARCH_PATHS 中 grep keyword，回傳檔案路徑清單。"""
    cmd = ["grep", "-rln", keyword] + [str(ROOT / p) for p in SEARCH_PATHS if (ROOT / p).exists()]
    for pat in EXCLUDE_PATTERNS:
        cmd += [f"--exclude={pat}"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return [line.strip() for line in out.stdout.splitlines() if line.strip()]
    except subprocess.TimeoutExpired:
        return []


def main() -> int:
    items = load_deprecated()
    if not items:
        print("✅ No deprecated features registered (.titi/deprecated_features.json 不存在或為空)")
        return 0

    violations: list[tuple[str, list[str]]] = []
    for it in items:
        key = it.get("key") or it.get("prd") or ""
        if not key:
            continue
        hits = grep_keyword(key)
        if hits:
            violations.append((key, hits))

    if not violations:
        print(f"✅ Spec drift check pass. {len(items)} deprecated keywords scanned, 0 殘留.")
        return 0

    print("❌ Spec drift detected — 已標記 deprecated 但仍有殘留:")
    for key, hits in violations:
        print(f"\n  {key}：{len(hits)} 處殘留")
        for h in hits[:10]:
            print(f"    - {h}")
        if len(hits) > 10:
            print(f"    ... (+{len(hits)-10} more)")
    print("\n參考 feedback_spec_deletion_sop.md 處理流程。")
    # CI 模式才 exit non-zero（避免本地誤跑阻塞）
    return 1 if "1" == (subprocess.os.environ.get("CI_FAIL_ON_DRIFT") or "") else 0


if __name__ == "__main__":
    sys.exit(main())
