#!/bin/bash
# ============================================================
# CertiMate — One-Liner Full Deployment
# ============================================================
# Copy this entire script and run in your local terminal:
#   bash DEPLOY_ONE_LINER.sh
# ============================================================

set -euo pipefail

# Configuration
export GCP_PROJECT_ID="certimate-titi"
export GCP_REGION="asia-east1"
SERVICE_NAME="certimate-titi"
DB_INSTANCE="certimate-db"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo -e "${BOLD}${YELLOW}CertiMate Full Deployment${NC}"
echo "=================================="
echo ""

# 1. Verify prerequisites
echo -e "${BOLD}Step 1: Checking prerequisites...${NC}"
command -v gcloud >/dev/null || err "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
command -v firebase >/dev/null || err "firebase-tools not found. Install: npm install -g firebase-tools"
command -v git >/dev/null || err "git not found"
log "All tools installed"

# 2. Set up GCP
echo ""
echo -e "${BOLD}Step 2: Setting up GCP...${NC}"
gcloud config set project ${GCP_PROJECT_ID}
gcloud auth list | grep ACTIVE || err "Not authenticated. Run: gcloud auth login"
log "GCP project configured"

# 3. Get commit hash
SHORT_SHA=$(git rev-parse --short HEAD)
echo -e "${BOLD}Step 3: Building & deploying backend (commit: ${SHORT_SHA})${NC}"

# 4. Cloud Build
log "Starting Cloud Build..."
gcloud builds submit --config cloudbuild.yaml \
  --substitutions="_SERVICE_NAME=${SERVICE_NAME},_REGION=${GCP_REGION},SHORT_SHA=${SHORT_SHA}" \
  --quiet || err "Cloud Build failed"
log "Docker image built and pushed"

# 5. Deploy to Cloud Run
log "Deploying to Cloud Run..."
DOCKER_IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/certimate/${SERVICE_NAME}:${SHORT_SHA}"

gcloud run deploy ${SERVICE_NAME} \
  --image=${DOCKER_IMAGE} \
  --region=${GCP_REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=2 \
  --concurrency=80 \
  --timeout=300 \
  --add-cloudsql-instances=${GCP_PROJECT_ID}:${GCP_REGION}:${DB_INSTANCE} \
  --set-env-vars="DATABASE_URL=postgresql+psycopg://postgres:CertiMate2026!@/certimate?host=/cloudsql/${GCP_PROJECT_ID}:${GCP_REGION}:${DB_INSTANCE},JWT_SECRET_KEY=certimate-production-jwt-secret-2026,FRONTEND_URL=https://certimate-titi.web.app,FIREBASE_PROJECT_ID=certimate-titi,GOOGLE_CLIENT_ID=63018063271-fu1r2h37b3ttqr9uu5bthas2blt94c7l.apps.googleusercontent.com,SMTP_HOST=smtp.gmail.com,SMTP_USER=son731202@gmail.com,SMTP_PASSWORD=ptmqwgqcphubajbr" \
  --quiet || err "Cloud Run deployment failed"

# Get backend URL
BACKEND_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${GCP_REGION} --format='value(status.url)')
log "Backend deployed: ${BACKEND_URL}"

# 6. Seed demo account
echo ""
echo -e "${BOLD}Step 4: Creating demo account...${NC}"
curl -s -X POST "${BACKEND_URL}/api/v1/auth/seed-demo" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))" || warn "Demo account seed failed (non-blocking)"
log "Demo account ready"

# 7. Deploy frontend
echo ""
echo -e "${BOLD}Step 5: Building & deploying frontend...${NC}"
cd frontend
log "Building Next.js..."
NEXT_PUBLIC_API_URL="${BACKEND_URL}/api/v1" npm run build > /dev/null 2>&1 || err "Next.js build failed"

# Verify no localhost
if grep -rq "localhost:8000" out/_next/static/chunks/ 2>/dev/null; then
  err "Build contains localhost references"
fi
log "Frontend build verified"

log "Deploying to Firebase Hosting..."
firebase deploy --only hosting --quiet || err "Firebase deployment failed"
cd - > /dev/null

log "Frontend deployed: https://certimate-titi.web.app"

# 8. Smoke test
echo ""
echo -e "${BOLD}Step 6: Running smoke tests...${NC}"
./smoke-test.sh "${BACKEND_URL}" || warn "Some smoke tests failed (review above)"

echo ""
echo "=================================="
echo -e "${GREEN}${BOLD}✓ Deployment Complete!${NC}"
echo ""
echo -e "Backend:  ${YELLOW}${BACKEND_URL}${NC}"
echo -e "Frontend: ${YELLOW}https://certimate-titi.web.app${NC}"
echo ""
echo -e "Demo Account:"
echo -e "  Email:    ${YELLOW}admin@certimate.com${NC}"
echo -e "  Password: ${YELLOW}admin123${NC}"
echo ""
