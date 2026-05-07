#!/bin/bash
# Pre-push hook — runs the same checks as the GitHub Actions gate locally.
# Install once with: ./scripts/install-hooks.sh
#
# Bypass with: git push --no-verify   (use sparingly; CI still runs)

set -e

# Read pushed refs to detect main pushes
protected_branch="main"
remote_name="$1"
while read -r local_ref local_sha remote_ref _remote_sha; do
  if [[ "$remote_ref" == "refs/heads/$protected_branch" ]]; then
    echo "🚪 Pre-push gate: pushing to $protected_branch"

    REPO_ROOT="$(git rev-parse --show-toplevel)"
    cd "$REPO_ROOT"

    echo "  [1/3] Step import lint…"
    (cd backend && python3 ../scripts/lint_step_imports.py) || {
      echo "❌ step import lint failed; push blocked"
      exit 1
    }

    echo "  [2/3] Backend behave (F35 + F36)…"
    (cd backend && .venv/bin/python -m behave \
        tests/features/35-API覆蓋補齊.feature \
        tests/features/36-資源硬刪除.feature 2>&1 | tail -5) || {
      echo "❌ behave failed; push blocked"
      exit 1
    }

    echo "  [3/3] Frontend tsc…"
    (cd frontend && npx tsc --noEmit) || {
      echo "❌ tsc failed; push blocked"
      exit 1
    }

    echo "✅ All gates passed."
  fi
done

exit 0
