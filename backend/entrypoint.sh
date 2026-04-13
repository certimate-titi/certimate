#!/bin/sh

echo "=== CertiMate Backend Startup ==="

# Run Alembic migrations (retry up to 3 times, non-fatal)
echo "Running database migrations..."
RETRY=0
MAX_RETRY=3
while [ $RETRY -lt $MAX_RETRY ]; do
    if python -m alembic upgrade head 2>&1; then
        echo "Migrations complete."
        break
    else
        RETRY=$((RETRY + 1))
        if [ $RETRY -lt $MAX_RETRY ]; then
            echo "Migration attempt $RETRY failed, retrying in 5s..."
            sleep 5
        else
            echo "WARNING: Migrations failed after $MAX_RETRY attempts. Starting server anyway..."
        fi
    fi
done

# Download historical questions from GCS (no DB needed, non-fatal)
echo "Downloading historical questions from GCS..."
python -c "
from app.scripts.sync_from_gcs import sync_from_gcs
result = sync_from_gcs()
print(f'  GCS: {result[\"downloaded\"]} downloaded, {result[\"skipped\"]} skipped, {len(result[\"errors\"])} errors')
" 2>&1 || echo "WARNING: GCS download failed (non-fatal)"

# Seed exam_subject_codes (idempotent, retry up to 3 times)
echo "Seeding exam_subject_codes..."
SEED_RETRY=0
while [ $SEED_RETRY -lt 3 ]; do
    if python -c "
from app.scripts.seed_exam_codes import seed_exam_codes
result = seed_exam_codes()
print(f'  Seed: {result}')
if 'error' in result:
    raise SystemExit(1)
" 2>&1; then
        echo "Exam codes seeded."
        break
    else
        SEED_RETRY=$((SEED_RETRY + 1))
        if [ $SEED_RETRY -lt 3 ]; then
            echo "Seed attempt $SEED_RETRY failed, retrying in 3s..."
            sleep 3
        else
            echo "WARNING: exam_subject_codes seed failed after 3 attempts."
        fi
    fi
done

# Start the server
echo "Starting Uvicorn on port ${PORT:-8080}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1
