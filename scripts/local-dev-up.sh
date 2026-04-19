#!/usr/bin/env bash
# Local dev startup — bring up Postgres + backend + frontend for Feature 33/34 QA.
#
# Usage:
#   ./scripts/local-dev-up.sh           # start everything
#   ./scripts/local-dev-up.sh --seed    # + seed super_admin users
#   ./scripts/local-dev-up.sh --stop    # stop everything
#
# Side effects:
# - Starts Docker container `certimate-local-db` (pgvector/pgvector:pg15 on :5433)
# - Runs alembic migrations
# - Optionally seeds users: super@certimate.com / admin@certimate.com / son731202@gmail.com
#   (all with password "admin123")
# - Starts uvicorn on :8000 in background
# - Starts Next.js on :3000 in background

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DB_CONTAINER="certimate-local-db"
DB_PORT=5433
DB_URL="postgresql+psycopg://postgres:postgres@localhost:${DB_PORT}/certimate-api_dev"
JWT_SECRET="local-dev-jwt-secret-feature-33-qa"

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

cmd_stop() {
  echo "⏹  Stopping services..."
  pkill -f "next dev" 2>/dev/null || true
  pkill -f "uvicorn app.main" 2>/dev/null || true
  docker stop "$DB_CONTAINER" 2>/dev/null || true
  echo "✓ stopped"
}

cmd_db_start() {
  if docker ps --filter "name=${DB_CONTAINER}" --format "{{.Names}}" | grep -q "$DB_CONTAINER"; then
    echo "✓ postgres already running"
    return
  fi
  if docker ps -a --filter "name=${DB_CONTAINER}" --format "{{.Names}}" | grep -q "$DB_CONTAINER"; then
    echo "▶  starting existing postgres container..."
    docker start "$DB_CONTAINER" > /dev/null
  else
    echo "▶  creating postgres container..."
    docker run -d --name "$DB_CONTAINER" \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=postgres \
      -e POSTGRES_DB=certimate-api_dev \
      -p ${DB_PORT}:5432 \
      pgvector/pgvector:pg15 > /dev/null
  fi

  # Wait for readiness
  for i in 1 2 3 4 5 6 7 8; do
    if docker exec "$DB_CONTAINER" pg_isready -U postgres 2>&1 | grep -q accepting; then
      echo "✓ postgres ready (after ${i}s)"
      return
    fi
    sleep 1
  done
  echo "❌ postgres failed to become ready"; exit 1
}

cmd_migrate() {
  echo "▶  running migrations..."
  cd "$BACKEND_DIR"
  DATABASE_URL="$DB_URL" .venv/bin/python -m alembic upgrade head 2>&1 | tail -3
}

cmd_seed_users() {
  echo "▶  seeding users..."
  cd "$BACKEND_DIR"
  DATABASE_URL="$DB_URL" .venv/bin/python - <<'PYEOF'
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User, UserRole, UserStatus, SubscriptionPlan
import os

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

engine = create_engine(os.environ["DATABASE_URL"])
Session = sessionmaker(bind=engine)
db = Session()

users = [
    ("super@certimate.com",    "Super Admin", UserRole.SUPER_ADMIN),
    ("admin@certimate.com",    "Admin",       UserRole.ADMIN),
    ("son731202@gmail.com",    "Simon",       UserRole.SUPER_ADMIN),
]
for email, name, role in users:
    u = db.query(User).filter(User.email == email).first()
    if u:
        u.role = role
        u.password_hash = hash_pw("admin123")
        u.status = UserStatus.ACTIVE
        u.subscription_plan = SubscriptionPlan.ULTRA
    else:
        u = User(
            email=email, password_hash=hash_pw("admin123"),
            display_name=name, role=role, status=UserStatus.ACTIVE,
            subscription_plan=SubscriptionPlan.ULTRA,
        )
        db.add(u)
    print(f"  ✓ {email} ({role.value})")
db.commit()
PYEOF
}

cmd_backend_start() {
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/me 2>/dev/null | grep -qE "200|401"; then
    echo "✓ backend already running"
    return
  fi
  echo "▶  starting backend on :8000..."
  cd "$BACKEND_DIR"
  DATABASE_URL="$DB_URL" JWT_SECRET_KEY="$JWT_SECRET" \
    nohup .venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
    > /tmp/certimate-backend.log 2>&1 &
  sleep 2
  for i in 1 2 3 4 5; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/me 2>/dev/null | grep -qE "200|401"; then
      echo "✓ backend ready (PID: $!)"
      return
    fi
    sleep 1
  done
  echo "⚠ backend may still be starting — check /tmp/certimate-backend.log"
}

cmd_frontend_start() {
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null | grep -qE "200|307"; then
    echo "✓ frontend already running"
    return
  fi
  echo "▶  starting frontend on :3000..."
  cd "$FRONTEND_DIR"
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 \
    nohup npm run dev > /tmp/certimate-frontend.log 2>&1 &
  sleep 3
  echo "✓ frontend PID: $! (log: /tmp/certimate-frontend.log)"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if [ "$1" = "--stop" ]; then
  cmd_stop
  exit 0
fi

cmd_db_start
cmd_migrate

if [ "$1" = "--seed" ] || [ "$2" = "--seed" ]; then
  cmd_seed_users
fi

cmd_backend_start
cmd_frontend_start

cat <<SUMMARY

═══════════════════════════════════════════════
🚀 CertiMate local dev ready
═══════════════════════════════════════════════
Frontend:  http://localhost:3000
Backend:   http://localhost:8000/api/v1
Postgres:  localhost:${DB_PORT} (user/pw: postgres/postgres)

Test accounts (password: admin123):
  super@certimate.com      (SUPER_ADMIN)
  admin@certimate.com      (ADMIN)
  son731202@gmail.com      (SUPER_ADMIN — supports Google SSO)

Logs:
  tail -f /tmp/certimate-backend.log
  tail -f /tmp/certimate-frontend.log

Stop everything:
  ./scripts/local-dev-up.sh --stop

SUMMARY
