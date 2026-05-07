#!/bin/bash
# One-time installer for local git hooks.
set -e

# Resolve the real .git/hooks dir (handles worktrees where .git is a file pointing
# to /path/to/main/.git/worktrees/<name>; hooks live in main repo's .git/hooks).
GIT_COMMON_DIR="$(git rev-parse --git-common-dir)"
HOOK_DIR="$GIT_COMMON_DIR/hooks"
SRC="$(git rev-parse --show-toplevel)/scripts/pre-push.sh"

cp "$SRC" "$HOOK_DIR/pre-push"
chmod +x "$HOOK_DIR/pre-push"
echo "✅ pre-push hook installed at $HOOK_DIR/pre-push"
echo "   bypass with: git push --no-verify"
