#!/bin/bash
# ============================================================
# CertiMate — Post-Deployment Smoke Test
# ============================================================
#
# Verifies critical API endpoints are responding correctly
# after a deployment.
#
# Usage:
#   ./smoke-test.sh                              # Use default URL
#   ./smoke-test.sh https://your-backend.run.app # Custom URL
# ============================================================

BASE_URL="${1:-https://certimate-titi-63018063271.asia-east1.run.app}"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

PASSED=0
FAILED=0
TOTAL=9  # 6.5 schema health 加在 Sprint 11

echo ""
echo -e "${BOLD}CertiMate Smoke Test${NC}"
echo -e "Target: ${YELLOW}${BASE_URL}${NC}"
echo "----------------------------------------"

# --- Helper ---
# check_endpoint NAME METHOD PATH EXPECTED_CODES [DATA]
#   EXPECTED_CODES: comma-separated list of acceptable HTTP status codes
check_endpoint() {
  local name="$1"
  local method="$2"
  local path="$3"
  local expected="$4"
  local data="${5:-}"

  local url="${BASE_URL}${path}"
  local status

  if [ "$method" = "POST" ] && [ -n "$data" ]; then
    status=$(curl -s -o /dev/null -w "%{http_code}" \
      -X POST \
      -H "Content-Type: application/json" \
      -d "$data" \
      --max-time 15 \
      "$url" 2>/dev/null)
  else
    status=$(curl -s -o /dev/null -w "%{http_code}" \
      --max-time 15 \
      "$url" 2>/dev/null)
  fi

  # Check if status is in the expected list
  local ok=false
  IFS=',' read -ra CODES <<< "$expected"
  for code in "${CODES[@]}"; do
    if [ "$status" = "$code" ]; then
      ok=true
      break
    fi
  done

  if $ok; then
    echo -e "  ${GREEN}Pass${NC}  ${name}  (HTTP ${status})"
    PASSED=$((PASSED + 1))
  else
    echo -e "  ${RED}FAIL${NC}  ${name}  (HTTP ${status}, expected ${expected})"
    FAILED=$((FAILED + 1))
  fi
}

# --- Tests ---

# 1. Available subjects — auth required, should not return 500
check_endpoint \
  "GET  /api/v1/subjects/available" \
  "GET" \
  "/api/v1/subjects/available" \
  "200,401,403"

# 2. Auth login — with bad credentials should return 400 or 401, NOT 500
check_endpoint \
  "POST /api/v1/auth/login" \
  "POST" \
  "/api/v1/auth/login" \
  "200,400,401,403,422" \
  '{"email":"smoke-test@example.com","password":"not-a-real-password"}'

# 3. Onboarding summary — auth required, should return 401 (not 500)
check_endpoint \
  "GET  /api/v1/onboarding/summary" \
  "GET" \
  "/api/v1/onboarding/summary" \
  "200,401,403"

# 4. Announcements — public endpoint, should return 200
check_endpoint \
  "GET  /api/v1/announcements" \
  "GET" \
  "/api/v1/announcements" \
  "200"

# 5. Dashboard without auth — should return 401 (auth middleware works)
check_endpoint \
  "GET  /api/v1/dashboard (no auth)" \
  "GET" \
  "/api/v1/dashboard" \
  "401,403"

# 6. Health check — should return 200
check_endpoint \
  "GET  /health" \
  "GET" \
  "/health" \
  "200"

# 6.5 Schema health — Sprint 11：deploy 後主動驗 alembic migration 完整套用
# 修復 PR #28 事故：deploy success 但 migration fail 導致 schema drift。
# 此檢查若 status != "healthy" 直接 FAIL deploy gate（PR 不該 merge 進壞版本）。
SCHEMA_RESP=$(curl -s --max-time 15 "${BASE_URL}/api/v1/admin/health/db-schema" 2>/dev/null)
SCHEMA_STATUS=$(echo "$SCHEMA_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
SCHEMA_VER=$(echo "$SCHEMA_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('alembic_version','?'))" 2>/dev/null || echo "?")
if [ "$SCHEMA_STATUS" = "healthy" ]; then
  echo -e "  ${GREEN}Pass${NC}  GET  /admin/health/db-schema  (alembic=$SCHEMA_VER)"
  PASSED=$((PASSED + 1))
else
  echo -e "  ${RED}FAIL${NC}  GET  /admin/health/db-schema  (status=$SCHEMA_STATUS, alembic=$SCHEMA_VER)"
  echo -e "  ${RED}      → Migration drift detected. Fix locally + redeploy.${NC}"
  echo "$SCHEMA_RESP" | python3 -c "
import sys,json
d=json.load(sys.stdin)
mt = d.get('missing_tables', [])
mc = d.get('missing_columns', [])
if mt: print(f'      missing tables: {mt}')
if mc: print(f'      missing columns: {mc}')
" 2>/dev/null || true
  FAILED=$((FAILED + 1))
fi

# 7. Login with demo account — should return 200 with JWT token
echo ""
echo -e "  ${YELLOW}Login Flow Tests${NC}"
LOGIN_BODY='{"email":"admin@certimate.com","password":"admin123"}'
LOGIN_RESULT=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$LOGIN_BODY" \
  --max-time 15 \
  "${BASE_URL}/api/v1/auth/login" 2>/dev/null)
LOGIN_STATUS=$(echo "$LOGIN_RESULT" | tail -1)
LOGIN_JSON=$(echo "$LOGIN_RESULT" | sed '$d')
LOGIN_TOKEN=$(echo "$LOGIN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ "$LOGIN_STATUS" = "200" ] && [ -n "$LOGIN_TOKEN" ]; then
  echo -e "  ${GREEN}Pass${NC}  POST /api/v1/auth/login (demo)  (HTTP ${LOGIN_STATUS}, got token)"
  PASSED=$((PASSED + 1))
else
  echo -e "  ${RED}FAIL${NC}  POST /api/v1/auth/login (demo)  (HTTP ${LOGIN_STATUS}, no token)"
  FAILED=$((FAILED + 1))
fi

# 8. GET /auth/me with token — should return 200 with user info
if [ -n "$LOGIN_TOKEN" ]; then
  ME_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $LOGIN_TOKEN" \
    --max-time 15 \
    "${BASE_URL}/api/v1/auth/me" 2>/dev/null)
  if [ "$ME_STATUS" = "200" ]; then
    echo -e "  ${GREEN}Pass${NC}  GET  /api/v1/auth/me (with token)  (HTTP ${ME_STATUS})"
    PASSED=$((PASSED + 1))
  else
    echo -e "  ${RED}FAIL${NC}  GET  /api/v1/auth/me (with token)  (HTTP ${ME_STATUS})"
    FAILED=$((FAILED + 1))
  fi
else
  echo -e "  ${RED}FAIL${NC}  GET  /api/v1/auth/me (skipped — no token from login)"
  FAILED=$((FAILED + 1))
fi

# --- Summary ---
echo "----------------------------------------"
if [ "$FAILED" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}Result: ${PASSED}/${TOTAL} passed${NC}"
else
  echo -e "${RED}${BOLD}Result: ${PASSED}/${TOTAL} passed, ${FAILED} failed${NC}"
fi
echo ""

exit "$FAILED"
