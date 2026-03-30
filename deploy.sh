#!/bin/bash
set -euo pipefail

# ============================================================
# CertiMate — Minimal Budget GCP Deployment Script
# ============================================================
#
# Architecture (estimated monthly cost):
#   Frontend : Firebase Hosting (free tier)           $0
#   Backend  : Cloud Run (scale-to-zero, free tier)   $0 ~ $5
#   Database : Cloud SQL PostgreSQL db-f1-micro        ~$7.67
#   Total    :                                        ~$8 ~ $13/mo
#
# Alternative: Use Neon/Supabase free PostgreSQL for $0 DB cost.
#
# Prerequisites:
#   1. gcloud CLI installed + authenticated
#   2. Firebase CLI installed (npm i -g firebase-tools)
#   3. GCP project created with billing enabled
#
# Usage:
#   ./deploy.sh                     # Full deploy (infra + backend + frontend)
#   ./deploy.sh backend             # Backend only
#   ./deploy.sh frontend            # Frontend only
#   ./deploy.sh infra               # Infrastructure only (DB, AR, IAM)
#   ./deploy.sh migrate             # Run DB migrations only
# ============================================================

# --- Configuration (edit these) ---
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-asia-east1}"
SERVICE_NAME="certimate-api"
DB_INSTANCE_NAME="certimate-db"
DB_NAME="certimate"
DB_USER="certimate"
DB_TIER="db-f1-micro"                  # Cheapest: ~$7.67/mo
AR_REPO="certimate"                     # Artifact Registry repo name

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1" >&2; exit 1; }

# --- Validate prerequisites ---
check_prereqs() {
  command -v gcloud >/dev/null 2>&1 || err "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
  [ -n "$PROJECT_ID" ] || err "Set GCP_PROJECT_ID env var: export GCP_PROJECT_ID=your-project-id"

  gcloud config set project "$PROJECT_ID" --quiet
  log "Using project: $PROJECT_ID, region: $REGION"
}

# --- Infrastructure Setup ---
setup_infra() {
  log "=== Setting up GCP infrastructure ==="

  # Enable required APIs
  log "Enabling APIs..."
  gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --quiet

  # Create Artifact Registry repository (if not exists)
  if ! gcloud artifacts repositories describe "$AR_REPO" --location="$REGION" &>/dev/null; then
    log "Creating Artifact Registry repository..."
    gcloud artifacts repositories create "$AR_REPO" \
      --repository-format=docker \
      --location="$REGION" \
      --description="CertiMate container images"
  else
    log "Artifact Registry repository already exists."
  fi

  # Create Cloud SQL instance (if not exists)
  if ! gcloud sql instances describe "$DB_INSTANCE_NAME" &>/dev/null; then
    log "Creating Cloud SQL PostgreSQL instance (${DB_TIER})..."
    log "This takes 3-5 minutes..."
    gcloud sql instances create "$DB_INSTANCE_NAME" \
      --database-version=POSTGRES_15 \
      --tier="$DB_TIER" \
      --region="$REGION" \
      --storage-type=HDD \
      --storage-size=10 \
      --no-assign-ip \
      --network=default \
      --quiet || {
        # If private IP fails (no VPC connector), use public IP
        warn "Private IP failed, creating with public IP instead..."
        gcloud sql instances create "$DB_INSTANCE_NAME" \
          --database-version=POSTGRES_15 \
          --tier="$DB_TIER" \
          --region="$REGION" \
          --storage-type=HDD \
          --storage-size=10 \
          --quiet
      }

    # Set password
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)
    gcloud sql users create "$DB_USER" \
      --instance="$DB_INSTANCE_NAME" \
      --password="$DB_PASSWORD"

    gcloud sql databases create "$DB_NAME" \
      --instance="$DB_INSTANCE_NAME"

    echo ""
    log "============================================="
    log "  Cloud SQL created!"
    log "  Instance: $DB_INSTANCE_NAME"
    log "  Database: $DB_NAME"
    log "  User: $DB_USER"
    log "  Password: $DB_PASSWORD"
    log "============================================="
    log "SAVE THIS PASSWORD! It won't be shown again."
    echo ""
  else
    log "Cloud SQL instance already exists."
  fi

  # Get Cloud SQL connection name
  CONNECTION_NAME=$(gcloud sql instances describe "$DB_INSTANCE_NAME" --format='value(connectionName)')
  log "Cloud SQL connection: $CONNECTION_NAME"

  log "Infrastructure setup complete."
}

# --- Deploy Backend ---
deploy_backend() {
  log "=== Deploying Backend to Cloud Run ==="

  # Get Cloud SQL connection name
  CONNECTION_NAME=$(gcloud sql instances describe "$DB_INSTANCE_NAME" --format='value(connectionName)' 2>/dev/null || echo "")

  if [ -z "$CONNECTION_NAME" ]; then
    err "Cloud SQL instance not found. Run: ./deploy.sh infra"
  fi

  # Build DATABASE_URL for Cloud SQL with Unix socket (Cloud Run <-> Cloud SQL)
  # Format: postgresql+psycopg://user:pass@/dbname?host=/cloudsql/connection-name
  if [ -z "${DB_PASSWORD:-}" ]; then
    echo ""
    warn "DB_PASSWORD not set. Enter the password from infra setup:"
    read -rsp "  Password: " DB_PASSWORD
    echo ""
  fi

  DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

  # JWT secret
  JWT_SECRET="${JWT_SECRET_KEY:-$(openssl rand -hex 32)}"

  # Build and push image
  log "Building Docker image..."
  IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${SERVICE_NAME}:latest"

  gcloud builds submit backend/ \
    --tag="$IMAGE" \
    --quiet

  # Deploy to Cloud Run
  log "Deploying to Cloud Run..."
  gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=2 \
    --concurrency=80 \
    --timeout=300 \
    --add-cloudsql-instances="$CONNECTION_NAME" \
    --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
    --set-env-vars="JWT_SECRET_KEY=${JWT_SECRET}" \
    --set-env-vars="DEBUG=false" \
    --quiet

  # Get URL
  BACKEND_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')
  log "Backend deployed: ${BACKEND_URL}"
  log "Health check: ${BACKEND_URL}/health"
  log "API docs: ${BACKEND_URL}/api/v1/docs"

  # Save URL for frontend
  echo "$BACKEND_URL" > .backend_url
}

# --- Deploy Frontend ---
deploy_frontend() {
  log "=== Deploying Frontend to Firebase Hosting ==="

  cd frontend

  # Read backend URL
  BACKEND_URL="${BACKEND_API_URL:-}"
  if [ -z "$BACKEND_URL" ] && [ -f "../.backend_url" ]; then
    BACKEND_URL=$(cat ../.backend_url)
  fi

  if [ -z "$BACKEND_URL" ]; then
    warn "BACKEND_API_URL not set. Frontend will use relative API paths."
  fi

  # Build
  log "Building Next.js (static export)..."
  NEXT_PUBLIC_API_URL="$BACKEND_URL" npm run build

  # Deploy
  log "Deploying to Firebase Hosting..."
  npx firebase deploy --only hosting

  cd ..
  log "Frontend deployed to Firebase Hosting."
}

# --- Run Migrations Only ---
run_migrations() {
  log "=== Running Database Migrations ==="

  CONNECTION_NAME=$(gcloud sql instances describe "$DB_INSTANCE_NAME" --format='value(connectionName)' 2>/dev/null || echo "")
  [ -n "$CONNECTION_NAME" ] || err "Cloud SQL instance not found."

  if [ -z "${DB_PASSWORD:-}" ]; then
    read -rsp "DB Password: " DB_PASSWORD
    echo ""
  fi

  # Use cloud-sql-proxy for local migration
  log "Starting Cloud SQL Auth Proxy..."
  cloud-sql-proxy "$CONNECTION_NAME" --port 5433 &
  PROXY_PID=$!
  sleep 3

  DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@localhost:5433/${DB_NAME}"
  cd backend
  DATABASE_URL="$DATABASE_URL" python -m alembic upgrade head
  cd ..

  kill $PROXY_PID 2>/dev/null || true
  log "Migrations complete."
}

# --- Main ---
check_prereqs

case "${1:-all}" in
  infra)
    setup_infra
    ;;
  backend)
    deploy_backend
    ;;
  frontend)
    deploy_frontend
    ;;
  migrate)
    run_migrations
    ;;
  all)
    setup_infra
    deploy_backend
    deploy_frontend
    ;;
  *)
    echo "Usage: $0 {infra|backend|frontend|migrate|all}"
    exit 1
    ;;
esac

log "Done!"
