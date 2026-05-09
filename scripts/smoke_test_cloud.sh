#!/usr/bin/env bash
# CertiMate (TiTi) — 雲端 smoke test 一鍵腳本
#
# 用途：每次 PR merge + deploy 後跑一次，幾秒內驗證所有關鍵 endpoint。
# 取代之前不可靠的 ScheduleWakeup + Cloud Logging 排查流程。
#
# 用法：
#   bash scripts/smoke_test_cloud.sh                    # 全部
#   bash scripts/smoke_test_cloud.sh email              # 只測 email/retention
#   bash scripts/smoke_test_cloud.sh cost               # 只測 cost
#   API_URL=https://staging-... bash scripts/smoke_test_cloud.sh   # 改環境
#
# 退出碼：0 全過 / 1 任一失敗
#
# 設計原則：
# - 每項測試獨立，失敗不中止後續
# - 每項列 ✅/❌ + 響應 status + 耗時
# - 自動取 admin token，不需手動帶
# - 結尾印彙總

set -uo pipefail

API_URL="${API_URL:-https://certimate-titi-nfwnajqofa-de.a.run.app/api/v1}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@certimate.com}"
ADMIN_PASS="${ADMIN_PASS:-admin123}"
FILTER="${1:-all}"

PASS=0
FAIL=0
SKIPPED=0

# Color codes
G='\033[0;32m'  # green
R='\033[0;31m'  # red
Y='\033[0;33m'  # yellow
B='\033[0;36m'  # cyan
N='\033[0m'

# ── helpers ─────────────────────────────────────────────────────────────────

_check() {
  local label="$1"; local expected="$2"; local actual="$3"; local extra="${4:-}"
  if [[ "$actual" == "$expected" ]]; then
    printf "  ${G}✅${N} %-40s %s %s\n" "$label" "$actual" "$extra"
    PASS=$((PASS+1))
  else
    printf "  ${R}❌${N} %-40s expected=%s got=%s %s\n" "$label" "$expected" "$actual" "$extra"
    FAIL=$((FAIL+1))
  fi
}

_skip() {
  printf "  ${Y}⏭${N}  %-40s skipped: %s\n" "$1" "$2"
  SKIPPED=$((SKIPPED+1))
}

_section() { printf "\n${B}━━ %s ━━${N}\n" "$1"; }

_curl_status() {
  curl -sS -o /tmp/_smoke_body -w "%{http_code}" "$@"
}

# ── login ───────────────────────────────────────────────────────────────────

_section "Login + Plan Claim"
LOGIN_RESP=$(curl -sS -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}")

TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('access_token',''))")
REDIRECT=$(echo "$LOGIN_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('redirect_to',''))")

if [[ -z "$TOKEN" ]]; then
  printf "${R}❌ login failed:${N} %s\n" "$LOGIN_RESP"
  exit 1
fi

PLAN_CLAIM=$(echo "$TOKEN" | python3 -c "
import json, base64, sys
tok = sys.stdin.read().strip()
payload = json.loads(base64.urlsafe_b64decode(tok.split('.')[1] + '==='))
print(payload.get('plan',''))
")

_check "JWT plan claim 含 ULTRA"     "ULTRA"   "$PLAN_CLAIM"
_check "登入 redirect_to 為 /today"   "/today"  "$REDIRECT"

AUTH="Authorization: Bearer $TOKEN"

# ── cost monitor ────────────────────────────────────────────────────────────

if [[ "$FILTER" == "all" || "$FILTER" == "cost" ]]; then
  _section "Cost Monitor"
  CODE=$(_curl_status "$API_URL/admin/cost/summary" -H "$AUTH")
  _check "GET /admin/cost/summary"          "200" "$CODE"

  CODE=$(_curl_status "$API_URL/admin/cost/by-feature?days=30" -H "$AUTH")
  TOTAL=$(python3 -c "import json; print(json.load(open('/tmp/_smoke_body')).get('total_usd',-1))" 2>/dev/null || echo "?")
  BUCKETS=$(python3 -c "import json; print(len(json.load(open('/tmp/_smoke_body')).get('buckets',[])))" 2>/dev/null || echo "?")
  _check "GET /admin/cost/by-feature"       "200" "$CODE" "(total=\$$TOTAL, buckets=$BUCKETS)"
fi

# ── retention email ─────────────────────────────────────────────────────────

if [[ "$FILTER" == "all" || "$FILTER" == "email" ]]; then
  _section "Retention Email (Sprint 9 議題E)"

  CODE=$(_curl_status "$API_URL/email/preferences" -H "$AUTH")
  _check "GET /email/preferences"           "200" "$CODE"

  CODE=$(_curl_status -X PUT "$API_URL/email/preferences" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d '{"daily_review_enabled":false}')
  _check "PUT /email/preferences (off)"     "200" "$CODE"

  CODE=$(_curl_status -X PUT "$API_URL/email/preferences" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d '{"daily_review_enabled":true}')
  _check "PUT /email/preferences (on)"      "200" "$CODE"

  CODE=$(_curl_status "$API_URL/email/unsubscribe?token=invalid_xxxxx")
  _check "GET /email/unsubscribe (invalid)" "400" "$CODE"

  CODE=$(_curl_status -X POST "$API_URL/admin/retention/run-daily-cron?trigger=daily_review" -H "$AUTH")
  SUMMARY=$(python3 -c "
import json
try:
  d = json.load(open('/tmp/_smoke_body'))
  print(f\"sent={d.get('sent','?')} skipped={d.get('skipped','?')} failed={d.get('failed','?')}\")
except: print('parse_fail')
" 2>/dev/null)
  _check "POST /admin/retention/run-daily-cron" "200" "$CODE" "($SUMMARY)"

  CODE=$(_curl_status "$API_URL/admin/retention/analytics?days=30" -H "$AUTH")
  _check "GET /admin/retention/analytics"   "200" "$CODE"
fi

# ── auth & today ────────────────────────────────────────────────────────────

if [[ "$FILTER" == "all" || "$FILTER" == "today" ]]; then
  _section "Today / Dashboard"
  CODE=$(_curl_status "$API_URL/dashboard/today" -H "$AUTH")
  _check "GET /dashboard/today"             "200" "$CODE"

  CODE=$(_curl_status "$API_URL/dashboard/confidence-calibration" -H "$AUTH")
  _check "GET /dashboard/confidence-calibration" "200" "$CODE"
fi

# ── knowledge map（migration schema 健康檢查）──────────────────────────────
# 這個 endpoint 撞 knowledge_nodes 表的 ORM 全 SELECT，能抓到 schema drift
# （embedding 欄位等）— PR #29 修正後加入此檢查防 regression
if [[ "$FILTER" == "all" || "$FILTER" == "knowledge" ]]; then
  _section "Knowledge Map (migration schema 健康檢查)"
  TEST_SUBJ="b0000003-0001-0001-0000-000000000001"
  CODE=$(_curl_status "$API_URL/knowledge-map/subjects/$TEST_SUBJ/nodes" -H "$AUTH")
  NODES_COUNT=$(python3 -c "import json; d=json.load(open('/tmp/_smoke_body')); print(len(d.get('nodes',[])))" 2>/dev/null || echo "?")
  _check "GET /knowledge-map/subjects/.../nodes" "200" "$CODE" "(nodes=$NODES_COUNT)"

  # 取第一個 node 測 N:M 端點
  if [[ "$NODES_COUNT" != "?" && "$NODES_COUNT" != "0" ]]; then
    NODE_ID=$(python3 -c "import json; d=json.load(open('/tmp/_smoke_body')); print(d['nodes'][0]['id'])" 2>/dev/null)
    if [[ -n "$NODE_ID" ]]; then
      CODE=$(_curl_status "$API_URL/knowledge-map/nodes/$NODE_ID/scaffolds" -H "$AUTH")
      _check "GET /knowledge-map/nodes/.../scaffolds (T85 N:M)" "200" "$CODE"
    fi
  fi
fi

# ── ai_model_routings (T72 verify, indirect) ────────────────────────────────

if [[ "$FILTER" == "all" || "$FILTER" == "routing" ]]; then
  _section "Plan-Tier Model Routing (T72)"
  # 沒有直接查 routing 表的 endpoint，間接驗：
  # 觸發一次有 task_type=advanced 的端點，看能否成功（routing fallback 都通則 OK）
  # admin 是 ULTRA，理論上 advanced → claude-sonnet-4-5
  _skip "ai_model_routings 驗證" "需真實 ai_coach_chat 流量，兩週後 by-feature 拉資料看 endpoint 欄位"
fi

# ── 最終彙總 ────────────────────────────────────────────────────────────────

printf "\n${B}━━ Summary ━━${N}\n"
printf "  ${G}✅ Pass: %d${N}    ${R}❌ Fail: %d${N}    ${Y}⏭ Skip: %d${N}\n" "$PASS" "$FAIL" "$SKIPPED"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
exit 0
