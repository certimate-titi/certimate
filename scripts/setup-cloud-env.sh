#!/bin/bash
# =============================================================
# CertiMate — Cloud Environment Setup Script
# =============================================================
# 用於 Claude Code Web (claude.ai/code) 的雲端環境自動設定。
# 在環境設定的「安裝腳本 (Setup Script)」欄位貼入此腳本，
# 每次開啟新 session 時會自動執行。
# =============================================================

set -e

echo "=== CertiMate Cloud Environment Setup ==="

# ---------------------------
# 1. 系統服務
# ---------------------------
echo "[1/5] Starting system services..."

# 啟動 PostgreSQL（雲端 VM 已預裝）
if command -v pg_isready &> /dev/null; then
  sudo service postgresql start 2>/dev/null || true
  echo "  ✓ PostgreSQL started"
else
  echo "  ⚠ PostgreSQL not found (will use Testcontainers)"
fi

# 啟動 Docker（Testcontainers 需要）
if command -v docker &> /dev/null; then
  sudo service docker start 2>/dev/null || true
  echo "  ✓ Docker started"
else
  echo "  ⚠ Docker not found"
fi

# ---------------------------
# 2. Python 後端環境
# ---------------------------
echo "[2/5] Setting up Python backend..."

cd "$CLAUDE_PROJECT_DIR/backend"

# 建立 venv（若不存在）
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "  ✓ Created Python venv"
fi

# 安裝依賴
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "  ✓ Python dependencies installed"

# ---------------------------
# 3. Node.js 前端環境
# ---------------------------
echo "[3/5] Setting up Node.js frontend..."

cd "$CLAUDE_PROJECT_DIR/frontend"

# 確保使用 Node.js 20+
if command -v nvm &> /dev/null; then
  nvm use 20 2>/dev/null || nvm use default
fi

npm install --silent 2>/dev/null
echo "  ✓ Node.js dependencies installed"

# ---------------------------
# 4. 環境變數檢查
# ---------------------------
echo "[4/5] Checking environment variables..."

cd "$CLAUDE_PROJECT_DIR"

REQUIRED_VARS=("DATABASE_URL" "JWT_SECRET_KEY")
OPTIONAL_VARS=("ANTHROPIC_API_KEY" "OPENAI_API_KEY" "GEMINI_API_KEY" "VOYAGE_API_KEY" "NEXT_PUBLIC_FIREBASE_API_KEY")

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    echo "  ⚠ Missing required: $var"
  else
    echo "  ✓ $var is set"
  fi
done

for var in "${OPTIONAL_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    echo "  ○ Optional not set: $var"
  else
    echo "  ✓ $var is set"
  fi
done

# ---------------------------
# 5. 驗證設定
# ---------------------------
echo "[5/5] Verifying setup..."

cd "$CLAUDE_PROJECT_DIR/backend"

# 驗證 Python 環境
PYTHON_VER=$(.venv/bin/python --version 2>&1)
echo "  ✓ Python: $PYTHON_VER"

# 驗證 FastAPI 可匯入
.venv/bin/python -c "import fastapi; print(f'  ✓ FastAPI: {fastapi.__version__}')" 2>/dev/null || echo "  ⚠ FastAPI import failed"

# 驗證 Node.js
cd "$CLAUDE_PROJECT_DIR/frontend"
NODE_VER=$(node --version 2>&1)
echo "  ✓ Node.js: $NODE_VER"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Quick start commands:"
echo "  Backend API:   cd backend && .venv/bin/python -m uvicorn app.main:app --reload"
echo "  BDD Tests:     cd backend && .venv/bin/python -m behave tests/features/ --tags=~@ignore"
echo "  Frontend Dev:  cd frontend && npm run dev"
echo ""

exit 0
